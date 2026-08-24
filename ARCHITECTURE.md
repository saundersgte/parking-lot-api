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
