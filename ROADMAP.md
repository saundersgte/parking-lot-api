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

## Current

- Terraform for the **Lambda execution role** — the runtime identity, and
  the mirror image of the deployment policy: four DynamoDB actions against
  one table ARN, nothing else.

## Next

- Terraform for Lambda, API Gateway and the CloudWatch log group. Two
  app-side prerequisites ride along: `mangum` is not installed yet, and
  `main.py` needs one line to expose the Lambda handler.
- A consistent validation and error-handling pass across every endpoint.
- Session history (`parking_sessions` table design) — deferred until after
  core CRUD is solid, per the sequencing decided in `ARCHITECTURE.md`.
- Deploy, test against the real AWS URL, then destroy and re-apply to
  prove the stack is idempotent. The README's deployment instructions get
  written during that run, by hand, while the steps are being performed.
- `README.md`, security review, cost review, mentor demo.
- At project end: delete the `parking-api-dev` access key — the only
  long-lived credential in the project.
