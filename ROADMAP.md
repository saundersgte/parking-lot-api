# Roadmap

Tracks progress against the plan in `parking_lot_api_brief.md` (section 23).
Updated as milestones complete, not on a fixed schedule.

## Completed

- Environment: Python 3.13 (matches the Lambda runtime), Terraform, and the
  AWS CLI installed. Git initialized with `.gitignore` written before any
  secret-bearing file could exist.
- Architecture decided and recorded in `ARCHITECTURE.md`: serverless
  (API Gateway + Lambda + DynamoDB) over containers, FastAPI + Mangum for
  one codebase that runs locally and in Lambda, full check-in/check-out
  session history built as an addition after core CRUD works.
- `GET /health` — working, verified with curl and FastAPI's `/docs` page.
- `Spot` data model (`app/models.py`) — a Pydantic model with `spot_id`
  and `status`, both text.
- In-memory storage (`app/storage.py`) — a plain dictionary standing in
  for a database, behind three functions (`save_spot`, `get_spot`,
  `list_spots`). This is the "seam": swapping in DynamoDB later should
  only touch this file, not the routes that call it.
- `POST /spots` — create a spot. Returns `201 Created`.
- `GET /spots` — list every spot currently stored.
- Verified end-to-end with curl: created a spot, listed it back, and
  observed firsthand that restarting the server (`--reload`) wipes
  in-memory data — the concrete reason a real database is coming.
- `GET /spots/{spot_id}` — fetch one spot by ID, `404` if it doesn't exist.
- Full CRUD complete: `PUT` and `DELETE /spots/{spot_id}`.
- Check-in / check-out endpoints and the `AVAILABLE` ⇄ `OCCUPIED` state
  machine — invalid transitions correctly rejected with `409 Conflict`.
- First automated test (`tests/test_spots.py`), using pytest's `TestClient`.
- Full pytest suite — 6 passing tests covering health, create, fetch one,
  missing-spot `404`, the full check-in/check-out cycle, and the `409`
  conflict on an invalid transition.

**Week 1 application work is complete.** Every endpoint is built, tested,
and committed.

### Week 2

- AWS access configured: a dedicated `parking-api-dev` IAM user (not root,
  not the admin user), with its access key stored in `~/.aws/credentials`
  — outside the repository, so it cannot be committed. Region `us-west-2`.
- First Terraform: `terraform/` holding `versions.tf` (pins the AWS
  provider to 6.x), `providers.tf` (region), and `main.tf` (the
  `parking_spots` DynamoDB table, on-demand billing, `spot_id` as
  partition key). `init`, `fmt`, `validate`, `plan`, and `apply` all run
  clean; `.terraform.lock.hcl` is committed, state and the provider cache
  are gitignored.
- `parking_spots` table live in AWS and confirmed `ACTIVE`.
- `app/storage.py` rewritten against DynamoDB using boto3 — `put_item`,
  `get_item`, `scan`, `delete_item` behind the same four function
  signatures as before. `main.py`, `models.py`, and `tests/` were not
  touched, which is exactly what the seam was built for.
- All 6 tests pass against the real table, and data now survives a server
  restart.
- Test isolation: `tests/conftest.py` holds an `autouse` fixture that
  clears every spot after each test, so the suite no longer leaves rows
  behind in a real AWS table.
- `ARCHITECTURE.md` gained a **Request flow** walkthrough — one check-in
  traced from arrival through routing, read, rule, write and response,
  plus which file owns which concern.
- Deployment identity scoped: `iam/deploy-policy.json`, a six-statement
  customer-managed policy covering Lambda, IAM (roles plus a
  condition-restricted `iam:PassRole`), API Gateway, CloudWatch Logs and
  DynamoDB. Every statement targets named resources (`parking-*`,
  `parking_*`); no bare `*` resource and no AWS-managed policy attached.
  Applied by hand in the console — reasoning recorded as Decision 5 in
  `ARCHITECTURE.md`. The DynamoDB statement is verified by the passing
  test suite; the other five are unexercised until the next `apply`.

- **Lambda execution role** in Terraform — the runtime identity, and the
  mirror image of the deployment policy: a trust policy allowing only
  `lambda.amazonaws.com` to assume it, and an inline policy granting four
  DynamoDB actions against one table ARN, plus writing to its own log group.
- CloudWatch log group declared explicitly (`/aws/lambda/parking-lot-api`)
  with 14-day retention, so `destroy` actually removes it rather than
  leaving an orphan Lambda created for itself.
- Lambda deployment: `mangum` installed, `handler = Mangum(app)` added to
  `main.py`, a separate `requirements-lambda.txt` for runtime-only
  dependencies, and a `build/` folder installed with
  `--platform manylinux2014_x86_64` so the compiled binaries are Linux
  rather than macOS. Zipped by Terraform's `archive_file` data source.
- Function verified in isolation before any HTTP wiring existed, by
  invoking it directly with hand-written API Gateway events — `/health`
  first (touches nothing), then `/spots` to prove the execution role could
  actually reach DynamoDB.
- API Gateway (HTTP API): the API, a Lambda integration, a `$default`
  catch-all route, a `$default` stage, and a resource-based
  `aws_lambda_permission` letting API Gateway invoke the function. FastAPI
  does the real routing; API Gateway forwards everything.
- **Full end-to-end verified over the public URL** — create, fetch,
  check-in, the 409 on a second check-in, check-out, a 404, and delete.
- **Idempotence proven.** Stack destroyed to nothing (verified against AWS,
  not just Terraform's state), then rebuilt from configuration alone into a
  working deployment. Done twice.
- `PUT /spots/{spot_id}` fixed: it previously trusted the body's `spot_id`
  over the URL's, so a mismatch silently wrote the wrong item. Now returns
  `400`, with a test covering it.
- Test coverage completed to the brief's section 15 list: update, delete and
  list had no tests at all, and the delete test asserts the row is actually
  gone afterwards rather than trusting the `204`. **Ten tests**, covering
  every endpoint and every error path, all verified against the live
  deployment as well as locally.
- `README.md` written — purpose, architecture, full API reference with
  worked examples, prerequisites, deployment, tests, cost, cleanup. The
  deployment and cleanup sections were written by hand while performing a
  real destroy-and-rebuild, so the steps are known to work.

**The project meets every item in the brief's Definition of Done.**

## Current

- Mentor demo.

## Next

- Replace the real AWS account ID in `iam/deploy-policy.json` with the
  `YOUR_ACCOUNT_ID` placeholder before the repo goes public — the README
  already instructs readers to substitute a placeholder that isn't there.
- Delete the `parking-api-dev` access key once the project is finished. It
  is the only long-lived credential in the project.

## Deliberately not done

- **Session history** (`parking_sessions`). Designed and documented in
  `ARCHITECTURE.md` Decision 3, not built. The assignment asks for
  check-in/check-out, which the state machine satisfies; history was an
  addition of my own and would have required `TransactWriteItems` for an
  atomic double-write.
- **Authentication**, multi-region, CI/CD, custom domains, WAF, X-Ray —
  listed as out of scope in `ARCHITECTURE.md`. The API is deliberately
  public and unauthenticated.
- A broader validation and error-handling pass. Pydantic covers request
  shape; `status` is free text rather than a constrained set of values.
- At project end: delete the `parking-api-dev` access key — the only
  long-lived credential in the project.
