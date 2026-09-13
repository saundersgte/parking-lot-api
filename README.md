# Parking Lot API

A small REST API for managing parking spots and vehicle check-in/check-out,
running on AWS with all infrastructure defined in Terraform.

Built as a mentor-assigned cloud engineering exercise. The aim was not only a
working API, but a deployment that can be explained — why this architecture,
what the alternatives were, and what each choice costs. Those decisions and
their trade-offs are recorded in `ARCHITECTURE.md`.

## Architecture

```
   curl / Postman
        |  HTTPS
        v
   API Gateway (HTTP API)    public URL + TLS. Forwards every request.
        |
        v
   Lambda (Python 3.13)      FastAPI app, wrapped by Mangum.
        |  boto3             Runs only during a request.
        v
   DynamoDB (on-demand)      parking_spots table, keyed on spot_id

   CloudWatch Logs  <- function output, 14-day retention
   IAM role         -> four DynamoDB actions, scoped to one table
```

Ten resources, all defined in `terraform/`. API Gateway does no routing of its
own — a single catch-all rule forwards everything to Lambda, and FastAPI
decides which function handles it.

Serverless was chosen over containers mainly because nothing here bills by the
hour, so the stack can stay deployed for demonstration at effectively no cost.
The full reasoning, including what that choice gives up, is in
`ARCHITECTURE.md`.

## API

A parking spot has two fields: `spot_id` (text) and `status` (text, either
`AVAILABLE` or `OCCUPIED`).

| Method | Path | Purpose | Success | Errors |
|---|---|---|---|---|
| GET | `/health` | Service check | 200 | — |
| POST | `/spots` | Create a spot | 201 | — |
| GET | `/spots` | List all spots | 200 | — |
| GET | `/spots/{spot_id}` | Fetch one spot | 200 | 404 |
| PUT | `/spots/{spot_id}` | Replace a spot | 200 | 400, 404 |
| DELETE | `/spots/{spot_id}` | Delete a spot | 204 | 404 |
| POST | `/spots/{spot_id}/check-in` | Park a vehicle | 200 | 404, 409 |
| POST | `/spots/{spot_id}/check-out` | Remove a vehicle | 200 | 404, 409 |

`400 Bad Request` means the request itself is malformed — on `PUT`, the
`spot_id` in the body not matching the one in the URL.

`404` means the spot does not exist.

`409 Conflict` means the request is valid and the spot exists, but its current
state makes the action invalid — checking into an `OCCUPIED` spot, or out of an
`AVAILABLE` one.

FastAPI also serves interactive documentation at `/docs`.

### Example requests

Create a spot:

```bash
curl -X POST https://YOUR-URL/spots \
  -H 'Content-Type: application/json' \
  -d '{"spot_id":"A1","status":"AVAILABLE"}'
```

```json
{"spot_id":"A1","status":"AVAILABLE"}
```

Check a vehicle in:

```bash
curl -X POST https://YOUR-URL/spots/A1/check-in
```

```json
{"spot_id":"A1","status":"OCCUPIED"}
```

Attempt it a second time — the state machine rejects it:

```bash
curl -X POST https://YOUR-URL/spots/A1/check-in
```

```json
{"detail":"Spot is not available"}
```

Returned with status `409`.

Check the vehicle out again:

```bash
curl -X POST https://YOUR-URL/spots/A1/check-out
```

```json
{"spot_id":"A1","status":"AVAILABLE"}
```

## Prerequisites

1. AWS Account with enough access to create an IAM user and policy (Root or existing admin)
2. AWS CLI installed and configured on your machine. "aws configure" with an access key, and region must be set to us-west-2 since providers.tf has this region hardcoded. If you wish to change the region, it must be updated in providers.tf.
3. Deployment policy attached in AWS - the `iam/deploy-policy.json` contents must be created as a customer-managed policy and attached to the user Terraform authenticates as. This file contains "YOUR_ACCOUNT_ID" placeholders which must be replaced with your 12-digit account number. For further context, reference ARCHITECTURE.md, Decision 5.
4. Terraform version 1.9 or newer must be installed. versions.tf requires this.
5. Python 3.13 must be installed. This build produces files named `cpython-313`, and the python3.13 runtime can't load binaries built by a different python version.
6. Virtual environment with the dev dependencies `pip install -r requirements.txt` into a `.venv` in order to run the test suite locally. Not required to deploy.

## Deployment

### Building the Deployment Package:
Lambda will need a zip containing the app and its libraries. There are two different requirements.txt files - requirements-lambda.txt and requirements.txt. 

requirements-lambda.txt is just for Lambda as it does not run pytest or httpx, uvicorn because API Gateway replaces it and boto3 because the runtime already has it. 

"--platform" in the command below was needed because I run on Mac, and omitting it will cause a deployment failure at runtime with a confusing import error.

This build step must be re-run after any change to `app/`, because terraform deploys `build/`, not your source. 

```bash
rm -rf build build.zip && mkdir build && source .venv/bin/activate && pip install -r requirements-lambda.txt -t build/ --platform manylinux2014_x86_64 --only-binary=:all: && cp -r app build/ && find build -name __pycache__ -type d -exec rm -rf {} +
```

### Initialize Terraform

This downloads the provider plugins listed in versions.tf. It is required one time per clone and it doesn't create anything in AWS, so it is safe to run anytime. 

```bash
cd terraform && terraform init
```
### Deploy the Stack

This will add all resources in the project to AWS. You must run the build step before apply, because Terraform zips the build/ folder and will fail or deploy an empty function if it isn't there.

```bash
terraform apply
```

### Get URL and verify the deployment

The URL that gets assigned contains a random ID that changes every time the stack is created and destroyed - therefore, do not hardcode this URL anywhere in the application. 

Get URL
```bash
terraform output api_url
```

Verify Deployment - make sure you replace "YOUR-URL" with the URL the previous step provided. 
```bash
curl https://YOUR-URL/health
curl https://YOUR-URL/spots
```

## Running the tests

The suite talks to the real DynamoDB table rather than a mock, so the stack
must be deployed and AWS credentials configured before it will run.

```bash
source .venv/bin/activate
python -m pytest -v
```

Seven tests: the health check, creating a spot, fetching one back, a `404` for
a spot that does not exist, a full check-in/check-out cycle, the `409` conflict
raised by checking in twice, and the `400` raised when a `PUT` body's `spot_id`
disagrees with the URL.

A fixture in `tests/conftest.py` deletes every spot after each test, so the
suite leaves the table exactly as it found it.

Testing against the real service is a deliberate trade. It is slower and it
requires credentials, but it exercises the actual IAM permissions and real
DynamoDB behaviour — a mock would happily pass while the deployed permissions
were wrong.

Note that `python -m pytest` is required rather than a bare `pytest`, and it
must be run from the project root: the `-m` form puts the current directory on
Python's import path so that `app` can be found.

## Cost

Roughly **$0.00–0.50/month** at demonstration traffic, and $0.00 while idle.

Nothing in this stack bills by the hour:

- **Lambda** — charged per invocation and per gigabyte-second of execution
  time. An idle function costs nothing at all.
- **DynamoDB** — `PAY_PER_REQUEST` (on-demand), charged per read and write.
  The alternative, provisioned capacity, bills hourly whether or not anything
  touches the table.
- **API Gateway** — HTTP API, charged per request and roughly 70% cheaper than
  the equivalent REST API.
- **CloudWatch Logs** — charged per gigabyte ingested and stored. The log group
  sets a 14-day retention; the default is to keep logs forever, which
  accumulates cost indefinitely and is an easy thing to forget.

The architecture deliberately avoids the services that charge while doing
nothing. The containerised alternative considered in `ARCHITECTURE.md` would
have needed a load balancer (~$16/month), Fargate (~$9/month), RDS
(~$12/month) and possibly a NAT gateway (~$32/month) — $50–70/month to run an
API nobody was calling.

`terraform destroy` removes every resource, returning the cost to zero.

## Cleanup
Removes all 10 resources. The DynamoDB table is deleted along with any data in is. This has been tested. The stack was destroyed and rebuilt from the configuration alone, producing a working deployment. 
```bash
terraform destroy
```