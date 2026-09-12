# Architecture

Decision record for the Parking Lot API. Each section states what was
chosen, what the alternative was, and what the choice costs.

---

## Chosen architecture

```
   curl / Postman
        |  HTTPS
        v
+---------------------+
|  API Gateway        |  public URL + TLS. Routes METHOD + /path
|  (HTTP API, v2)     |  to the Lambda function.
+----------+----------+
           |  invokes with an "event" dict
           v
+---------------------+
|  Lambda             |  FastAPI app, wrapped by Mangum.
|  (Python 3.13)      |  Runs only during a request.
+----------+----------+  Gets AWS permissions from an IAM role.
           |  boto3
           v
+---------------------+
|  DynamoDB           |  parking_spots   (current state, mutated)
|  (on-demand)        |  parking_sessions (history, append-only)
+---------------------+

CloudWatch Logs  <- all function output and errors
IAM role/policy  -> grants access to exactly these two tables
```

---

## Request flow — one check-in, end to end

Tracing `POST /spots/A1/check-in`:

1. **Arrival.** Locally, uvicorn accepts the HTTP request on port 8000. In
   AWS, API Gateway terminates TLS at the public URL and invokes Lambda
   with the request packed into an *event* dictionary, which Mangum
   unpacks back into an ordinary HTTP request. *(Not built yet.)*
   Everything below this step is identical in both environments.
2. **Routing.** FastAPI matches the method and path against its routing
   table — assembled at import time, when each `@app.post(...)` decorator
   ran — and calls `check_in(spot_id="A1")` in `app/main.py`.
3. **Read.** The route calls `storage.get_spot("A1")`, which issues a
   DynamoDB `GetItem` against `parking_spots`, keyed on the partition key.
   boto3 signs that request with credentials it resolved on its own. A
   missing item comes back as `None`, and the route raises `404`.
4. **Business rule.** The route checks `spot.status != "AVAILABLE"` and
   raises `409 Conflict` if the spot is already taken. The state machine
   lives here — not in the database, and not in the model.
5. **Write.** `spot.status = "OCCUPIED"`, then `storage.save_spot(spot)`
   issues a `PutItem`, which replaces the whole item.
6. **Response.** The route returns the `Spot`; Pydantic serialises it to
   JSON and FastAPI sends `200 OK`. In AWS, Mangum converts that into the
   response shape API Gateway expects.

Where each concern lives:

| Concern | Where |
|---|---|
| HTTP shape — paths, methods, status codes | `app/main.py` |
| Input validation | `app/models.py` |
| Business rules and state transitions | `app/main.py` routes |
| Persistence | `app/storage.py` |

Nothing above `storage.py` knows DynamoDB exists. That is why swapping the
in-memory dictionary for a real database changed one file and left every
route and every test untouched.

---

## Decision 1 — Serverless over containers

**Chosen:** API Gateway (HTTP API) -> Lambda -> DynamoDB
**Alternative:** ALB -> ECS Fargate -> RDS Postgres

| | Serverless | Containers |
|---|---|---|
| Idle cost | **$0.00/mo** | ~$25-70/mo |
| Load balancer | not required | ~$16/mo, billed hourly regardless of traffic |
| Compute idle | $0 | ~$9/mo Fargate |
| Database idle | $0 | ~$12/mo RDS after free tier |
| NAT Gateway | not required | ~$32/mo if private subnets |
| Terraform resources | ~8 | ~25+ (VPC, subnets, routes, SGs, IGW...) |
| Components that can fail | 3 | ~7 |

**Why:** An ALB bills per hour whether or not a request arrives. This
project should stay deployed so it can be demonstrated and linked from a
portfolio; serverless makes that free, containers make it a monthly bill.

The second reason is debugging surface. Containers would mean learning
VPC networking simultaneously with Terraform and Python. When a request
times out across seven components, the cause is ambiguous. Three
components is a project that finishes in two weeks.

**What this costs:**
- **AWS lock-in.** Lambda and DynamoDB are not portable. A container
  running FastAPI would move to any cloud unchanged.
- **No ad-hoc queries.** DynamoDB has no `SELECT ... WHERE`. Every access
  pattern must be designed into the keys up front.
- **Cold starts.** An idle function takes ~1s extra on its first request.
  Irrelevant here; would matter for a latency-sensitive service.

Accepted, because this is a low-traffic CRUD service. The same trade
would be wrong for a system needing relational reporting or portability.

---

## Decision 2 — FastAPI + Mangum over a raw Lambda handler

**Chosen:** a normal FastAPI application, adapted for Lambda by Mangum.
**Alternative:** `def lambda_handler(event, context)` parsing the event
dict and returning a response dict by hand.

**Why:** The raw handler cannot be run locally. Development would mean
deploying to AWS to test every change, which conflicts with the
local-first plan (build and prove the application before any cloud
exists, so an application bug can never be confused for an
infrastructure bug).

FastAPI also provides request validation via Pydantic, correct status
codes, and generated interactive docs at `/docs` — all of which would
otherwise be hand-written.

**What this costs:** one adapter layer between the AWS event and the
application. Mitigated by logging and reading a real API Gateway event
during deployment, so the translation is understood rather than assumed.

---

## Decision 3 — Retain session history

**Chosen:** two tables. `parking_spots` holds current state;
`parking_sessions` records every completed and in-progress stay.
**Alternative:** one table, where check-out simply erases the vehicle.

**Why:** "How long was that car here?", occupancy over time, and any
future billing all require history. Erasing it at check-out makes those
questions permanently unanswerable.

It also models a distinction worth learning: `parking_spots` items are
**mutated in place**, while `parking_sessions` items are an
**append-only log**. These have different key designs and different
access patterns.

**What this costs — and how it is handled:**

Check-in must now write twice: mark the spot occupied *and* open a
session. A partial failure would leave a car parked with no arrival
record — corruption that no later request can repair.

Resolved with `TransactWriteItems`, which commits both writes atomically
and carries a condition (`only if the spot is still AVAILABLE`). The same
call also prevents two vehicles claiming one spot concurrently, without
any locking.

**Sequencing:** sessions are built *after* CRUD and state transitions are
working and tested, as an additive feature rather than part of the
foundation. This keeps the hardest DynamoDB concept out of the way until
the application already works.

---

## Decision 4 — `Scan` for listing spots

**Chosen:** `GET /spots` calls DynamoDB's `Scan`.
**Alternative:** a global secondary index, or a separate index item
holding every spot ID.

**Why:** "list every spot" has no partition key to look up by — it is
inherently a full-table read. DynamoDB offers no cheaper equivalent of
`SELECT * FROM spots`.

**What this costs:**
- `Scan` reads and bills for every item in the table, not just the ones
  returned.
- A single `Scan` returns at most **1 MB**. Past that it returns a
  `LastEvaluatedKey` and the caller must request the next page.
  `list_spots()` does not paginate; it returns the first page only.

Accepted at this scale. A parking lot holds tens of spots at roughly 50
bytes each — the 1 MB ceiling is orders of magnitude beyond anything this
project will store. It is recorded because it is a genuine defect at a
scale this project will never reach, and the fix (a pagination loop)
belongs in the code when the data justifies it, not before.

---

## Decision 5 — Two identities, one of them applied by hand

**Chosen:** two separate IAM identities. A long-lived user,
`parking-api-dev`, holds *deployment* permissions and is configured by
hand in the console. A Lambda execution role, created by Terraform, holds
*runtime* permissions.
**Alternative:** a single identity used for both, or managing the
deployment user's own policy in Terraform alongside everything else.

**Why two:** they need opposite scopes. Deploying must be able to create
IAM roles, Lambda functions, an HTTP API and a log group — inherently
broad, because provisioning infrastructure requires it. Running only ever
performs four operations against one table. Collapsing them would drag the
narrow case up to the broad one, leaving a public web application holding
permission to create IAM roles.

**Why the deployment policy is not in Terraform:** Terraform authenticates
*as* that user. A configuration that manages its own credentials can
revoke its own access part-way through an apply, and recovery requires the
root account. So bootstrap identity is hand-applied, and version-controlled
as documentation in `iam/deploy-policy.json`; everything the project
*builds* stays Terraform-managed. The README states the manual step
explicitly rather than pretending the deployment is fully automated.

**Scoping, and where it stops:** no AWS-managed policy is attached, and
almost every statement targets named resources — `function:parking-*`,
`role/parking-*`, `table/parking_*`, `log-group:/aws/lambda/parking-*`.
`iam:PassRole` carries a condition restricting it to
`lambda.amazonaws.com`, so the execution role cannot be attached to any
other service; without that condition this key could grant a compute
instance whatever permissions it liked.

Two statements cannot be scoped that tightly, and both are deliberate:

- **API Gateway** puts generated IDs rather than chosen names into its
  ARNs, so there is no project-specific prefix to match. That statement is
  scoped to the service instead.
- **`logs:DescribeLogGroups`** requires `Resource: "*"`. It is a *list*
  operation — it asks which groups exist, a question that names no
  particular group — so AWS evaluates it against an empty log-group ARN
  that no prefix pattern can match. Discovered the direct way: the first
  `apply` failed with `AccessDenied` on exactly this call.

  The response was to isolate it. `DescribeLogGroups` sits alone in its own
  statement on `"*"`, while the six log actions that *can* be scoped stay
  restricted to `/aws/lambda/parking-*`. Granting one read-only list call
  broadly is a far smaller concession than widening the whole statement.

This is the general shape of the problem: list and describe operations
usually cannot be resource-scoped, because at the moment of the call no
resource has been named yet. The discipline is to grant them individually
rather than to give up on scoping.

**What this costs:**
- One manual step in an otherwise reproducible deployment.
- A long-lived access key on a laptop — the only non-temporary credential
  in the project. Mitigated by narrow scope, and by deleting the key once
  the project is finished. IAM Identity Center issuing short-lived
  credentials would remove it entirely and would be the correct choice on
  a team; it is deliberate overhead to skip for a two-week exercise.

---

## Configuration — how the application finds the table

`app/storage.py` reads the table name from the `SPOTS_TABLE` environment
variable, falling back to `parking_spots` when it is unset. Locally
nothing sets it, so the default applies and no configuration is needed to
run the app or the tests. In AWS, Terraform sets `SPOTS_TABLE` on the
Lambda function, so the deployed code targets whichever table Terraform
actually created. The name is never hardcoded in application code.

Credentials follow the same principle, and are never passed to boto3 at
all. The SDK resolves them itself: `~/.aws/credentials` when running
locally, the execution role's automatically-injected temporary
credentials when running in Lambda. The line `boto3.resource("dynamodb")`
is byte-identical in both environments — there is no `if production:`
branch anywhere in the codebase.

---

## Security posture

- **No credentials anywhere.** Lambda assumes an IAM role; AWS injects
  temporary credentials at runtime. There is no key to leak or rotate.
- **Least privilege.** The execution policy grants only the specific
  DynamoDB actions used, scoped to these two table ARNs. No wildcards,
  no `AdministratorAccess`.
- **Input validation** at the edge via Pydantic models; malformed
  requests are rejected before reaching business logic.
- **No internal error leakage.** Unhandled exceptions return a generic
  message; detail goes to CloudWatch Logs only.
- **State files are never committed.** Terraform state stores attribute
  values in plaintext.

## Deliberately out of scope

Authentication, multi-region, CI/CD, custom domains, WAF, X-Ray. This is
a two-week scoped exercise; each is noted here as a known omission rather
than an oversight.

## Cost controls

- DynamoDB `PAY_PER_REQUEST` — provisioned capacity bills hourly at zero
  traffic.
- CloudWatch log groups get explicit `retention_in_days`; the default is
  "never expire", which accumulates cost indefinitely.
- HTTP API rather than REST API — roughly 70% cheaper and sufficient here.

Estimated total: **$0.00-0.50/month.**
