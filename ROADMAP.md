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

## Current

- pytest suite: CRUD, both state transitions, every error path. One test
  written (`test_health`); the rest still to come.

## Next

- A consistent validation and error-handling pass across every endpoint.
- Session history (`parking_sessions` table design) — deferred until after
  core CRUD is solid, per the sequencing decided in `ARCHITECTURE.md`.
- Swap in-memory storage for DynamoDB.
- Terraform: DynamoDB table, IAM role/policy, Lambda, API Gateway, log group.
- Deploy, test against the real AWS URL, then destroy and re-apply to
  prove the stack is idempotent.
- `README.md`, security review, cost review, mentor demo.
