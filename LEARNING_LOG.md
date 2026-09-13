# Learning Log

Per-concept record, per `parking_lot_api_brief.md` section 19. Concept/Why/
What/How are filled in as things come up. "What I understand" and "What I
still need to learn" are mine to fill in — nobody else can honestly answer
those for me.

---

## Virtual environments (`venv`)

**Why we needed it:** installing FastAPI into my machine's shared Python
would mix this project's dependencies with every other Python project on
the laptop.
**What it does:** creates an isolated folder with its own library shelf,
sealed off from the system-wide Python.
**How we used it:** `python3.13 -m venv .venv`, then `source .venv/bin/activate`
at the start of every session.
**What I understand:** running apps within virtual environment is essentially creates its own independent instance, separate from other files, projects, applications etc on my computer. 
**What I still need to learn:** how to continually manage, operate, create these environments from scratch. 

---

## Git and `.gitignore`

**Why we needed it:** version history, and a way to guarantee secrets
(Terraform state, `.env` files) can never accidentally get saved.
**What it does:** `git init` starts tracking history; `.gitignore` lists
patterns git refuses to save, checked before every commit.
**How we used it:** wrote `.gitignore` before any file existed that could
contain a secret, then verified rules with `git check-ignore -v` rather
than assuming they worked.
**What I understand:** 
**What I still need to learn:** how to setup, continually manage, and actively utilize these files and functions

---

## Decorators (`@app.get(...)`)

**Why we needed it:** FastAPI needs a way to connect a URL + HTTP method
to a specific Python function.
**What it does:** `@thing` is shorthand for `func = thing(func)` — a
normal function call, just written above the function instead of after it.
**How we used it:** `@app.get("/health")` above `health_check` files that
function into FastAPI's internal routing table, keyed by path and method.
**What I understand:**
**What I still need to learn:**

---

## Pydantic models and type hints

**Why we needed it:** a plain dictionary accepts any garbage without
complaint; incoming API data needs to be checked before we trust it.
**What it does:** a class inheriting from `BaseModel`, with `name: type`
lines, declares required fields and their types. Pydantic validates
automatically and raises a precise error if the data doesn't match.
**How we used it:** `Spot(BaseModel)` with `spot_id: str` and `status: str`
in `app/models.py`; FastAPI uses it to parse and validate incoming
request bodies automatically.
**What I understand:** that this is a way to classify key's value types and for the system to validate if a response is valid or not given the designated format
**What I still need to learn:** all the format types that can be used and when and where to use something like this from memory

---

## Dictionaries as storage, and the storage "seam"

**Why we needed it:** something has to hold created spots between
requests, before a real database exists.
**What it does:** `app/storage.py` wraps a plain dict behind three
functions (`save_spot`, `get_spot`, `list_spots`). Routes call the
functions, never the dict directly.
**How we used it:** proved live that restarting `uvicorn --reload` wipes
the dict — data only lives in memory, gone the moment the process
restarts. This is the exact problem DynamoDB solves later, and because
routes only ever call the functions, swapping the dict for DynamoDB
shouldn't require touching `main.py` at all.
**What I understand:** that this is temporary memory and dictionaries & data need to be rebuilt each time for the functions to work, until a proper db is put in place
**What I still need to learn:** understanding of how to build these things from memory to achieve the end goal 

---

## HTTP status codes and REST verbs

**Why we needed it:** a response needs to say more than just "it worked" —
callers need to know *what kind* of thing happened.
**What it does:** `GET` reads, `POST` creates. `200` = success, `201` =
success and something new now exists, `204` = success with deliberately
no body, `404` = the thing doesn't exist, `409` = the request is valid
but the resource's current state makes it invalid right now.
**How we used it:** `status_code=201` on create, `status_code=204` on
delete (no `return`), `404` when a spot ID isn't found, `409` when
check-in/check-out is attempted on a spot already in that state.
**What I understand:** i understand most of the codes and their purposes/ use cases
**What I still need to learn:** how to use them actively when testing and creating for troubleshooting and verification

---

## Automated testing: pytest, TestClient, assert

**Why we needed it:** manually re-running curl commands after every
change doesn't scale, and proves nothing stays working once something
new gets added.
**What it does:** `TestClient(app)` wraps the FastAPI app so a test can
send it fake requests directly in memory, no real server required.
`assert condition` fails that one test immediately if the condition is
false; every other `test_` function still runs independently.
**How we used it:** `tests/test_spots.py`, testing `/health` with two
assertions (status code and body). Run with `python -m pytest -v` —
plain `pytest` fails here because it doesn't add the project folder to
Python's import search list, so it can't find `app`.
**What I understand:** that this testing process runs temporary / fake requests in memory. this is good for short term tests while building 
**What I still need to learn:** how to replicate this process from memory or what tests to build exactly when building an application

---

## Reading Python errors

**Why we needed it:** most of the time spent building isn't writing new
code, it's working out why the code already written isn't doing what was
expected.
**What it does:** each error type points at a different kind of mistake,
and the message names the exact file and line:
- `SyntaxError: expected ':'` — a missing colon on a `def`/`if`/`for`.
- `SyntaxError: invalid syntax` on an `assert` — usually `=` (assign)
  where `==` (compare) belongs.
- `NameError: name 'x' is not defined` — a misspelled variable.
- `ModuleNotFoundError: No module named 'app'` — Python searched its list
  of folders and found nothing by that name. Usually means the command
  was run from the wrong directory.
- A test failure like `assert 404 == 200` — the code ran fine; it just
  produced a different answer than expected.
**How we used it:** hit all five of these in one session and worked
through each from the message alone. Also found a duplicate `test/`
folder created by a stale editor tab still pointing at the old path.
**What I understand:** how to scan through error codes and start looking for key identifiers > review code for what may possibly be causing that
**What I still need to learn:** further understanding terminology that python error codes use by default

---

## DynamoDB: items, attributes, and the partition key

**Why we needed it:** the dictionary in `storage.py` vanished every time
the server restarted. Data has to outlive the process that created it.
**What it does:** DynamoDB is a managed NoSQL database. A table holds
*items* (roughly a row), items hold *attributes* (roughly a field).
Unlike SQL there is no fixed column list — the only thing declared up
front is the key. The **partition key** is the value DynamoDB hashes to
decide where to physically store an item, which is how it finds it again
instantly.
**How we used it:** one table, `parking_spots`, with `spot_id` as its
partition key — the same key the dictionary was already using. `status`
is never declared anywhere; it simply gets written onto the item. The
same concept carries three names: Terraform says `hash_key`, the AWS API
says `HASH`, the AWS docs say "partition key".
**What I understand:**
**What I still need to learn:**

---

## `Scan`, and DynamoDB's missing `WHERE` clause

**Why we needed it:** `GET /spots` has to return every spot, but there is
no key to look one up by — "all of them" isn't a key.
**What it does:** `Scan` reads every item in the table. DynamoDB has no
equivalent of `SELECT * FROM spots`; you either fetch by key, or you read
everything. A single `Scan` returns at most 1 MB, after which it hands
back a `LastEvaluatedKey` and expects the caller to ask for the next page.
**How we used it:** `list_spots()` calls `scan()` and does not paginate.
Recorded in `ARCHITECTURE.md` as a real defect that this project's data
volume will never reach — tens of spots at ~50 bytes each against a 1 MB
ceiling.
**What I understand:**
**What I still need to learn:**

---

## boto3 and the credential provider chain

**Why we needed it:** Python has no built-in way to talk to AWS, and
hardcoding an access key in the source would be the exact thing the brief
forbids.
**What it does:** boto3 is AWS's Python SDK (named after the Amazon river
dolphin — not an acronym). Given no credentials, it searches in order:
environment variables, then `~/.aws/credentials`, then the IAM role of
whatever it happens to be running on.
**How we used it:** `boto3.resource("dynamodb")` with no arguments about
keys or region. Locally it finds `~/.aws/credentials`; inside Lambda it
will find the execution role's temporary credentials. The line is
identical in both places — there is no `if production:` anywhere in the
codebase. We also chose `resource` over `client` because `resource`
accepts plain Python values, while `client` requires DynamoDB's raw wire
format (`{"S": "A1"}` for a string).
**What I understand:**
**What I still need to learn:**

---

## Terraform: providers, resources, and state

**Why we needed it:** infrastructure created by clicking around a console
can't be reviewed, repeated, or destroyed reliably. The brief requires the
final stack be defined entirely in code.
**What it does:** `.tf` files are a *description of desired state*, not a
script executed top to bottom. A **provider** is a plugin that knows one
platform's API; a **resource** is one thing to create. **State** is
Terraform's private record of what it built, so it can compare desired
against actual and act on the difference.
**How we used it:** `versions.tf` pins the AWS provider to 6.x, so a
breaking upstream release can't silently change things. `providers.tf`
sets the region. `main.tf` declares one `aws_dynamodb_table`. Worth
keeping straight: `resource "aws_dynamodb_table" "parking_spots"` contains
three separate names — the *type* (decides what AWS builds), a *local
handle* AWS never sees, and the `name` argument (the actual table name).
**What I understand:**
**What I still need to learn:**

---

## `plan` before `apply`

**Why we needed it:** running a command that changes real infrastructure
without knowing what it will do is how people delete production.
**What it does:** `init` downloads the provider and writes
`.terraform.lock.hcl` (the exact version + checksums — this one gets
committed). `fmt` reformats files. `validate` checks the config offline.
`plan` compares config against state against reality, prints the
difference, and stops. `apply` does it for real. `destroy` removes it.
**How we used it:** the plan showed `Plan: 1 to add, 0 to change, 0 to
destroy` — that summary line is the habit worth keeping, and the destroy
count is the number to read first. Many fields showed
`(known after apply)`, which means AWS assigns that value and it cannot
exist yet, not that something is missing.
**What I understand:**
**What I still need to learn:**

---

## pytest fixtures and `conftest.py`

**Why we needed it:** once storage became a real database, tests stopped
being self-contained — they left rows sitting in AWS after finishing.
**What it does:** a **fixture** is setup/teardown code that runs *around*
a test rather than inside it. `conftest.py` is a filename pytest
discovers automatically, so fixtures defined there apply without any test
importing them. `autouse=True` applies it to every test without being
asked for. In a fixture, `yield` splits the function: everything before
runs before the test, everything after runs once it finishes.
**How we used it:** `tests/conftest.py` has nothing before the `yield` and
a cleanup loop after it, deleting every spot via our own `list_spots` and
`delete_spot`. Verified the table was empty afterwards with a real scan.
**What I understand:**
**What I still need to learn:**

---

## Saving a file vs staging it in git

**Why we needed it:** a commit came out missing `ARCHITECTURE.md` even
though the file was saved, which looked like the edits had been lost.
**What it does:** saving writes to disk; `git add` copies the disk version
into a staging area; `git commit` snapshots the staging area. Three
separate steps. `git status --short` prints two columns — column 1 is the
staging area (green), column 2 is the working tree (red). A leading space
plus a red `M` means "modified on disk, nothing staged."
**How we used it:** read the two-column output, confirmed with
`git show --stat` that the commit genuinely didn't contain the file, and
verified the content was still intact before re-staging it.
**What I understand:**
**What I still need to learn:**

---

## Deployment identity vs runtime identity

**Why we needed it:** "apply least privilege" sounds like one rule, but
applying it to the wrong identity locks you out of your own deployment.
**What it does:** two different identities exist, needing opposite
treatment. The **deployment identity** (`parking-api-dev`, used by
Terraform from the laptop) must be able to *create* infrastructure — IAM
roles, Lambda functions, API Gateway, log groups — so it is inherently
broad. The **runtime identity** (the Lambda execution role, created by
Terraform) is what the code authenticates as while serving a request, and
should be scoped to exactly the actions the application performs.
**How we used it:** `parking-api-dev` was created with DynamoDB access
and its access key stored in `~/.aws/credentials`, outside the repo where
git cannot reach it. Least privilege doesn't prevent a key from leaking —
it caps what a leaked key can do.
**What I understand:**
**What I still need to learn:**

---

## Writing an IAM policy by hand

**Why we needed it:** `parking-api-dev` could only touch DynamoDB, so
Terraform would have failed the moment it tried to create a Lambda
function. The obvious fix — attaching `AWSLambda_FullAccess` and
`IAMFullAccess` — would have given that key the ability to mint itself an
administrator role.
**What it does:** a policy is a list of statements. Each statement answers
three questions, and sometimes a fourth:
- `Effect` — Allow or Deny.
- `Action` — which API calls, written `service:ApiCall`.
- `Resource` — which things those calls may touch, as an ARN.
- `Condition` — optional. "Allow this, but only when…".

`Sid` is just a human-readable label with no effect on permissions.
`"Version": "2012-10-17"` is the name of the policy language itself, not a
date to update.
**How we used it:** `iam/deploy-policy.json`, six statements covering
Lambda, IAM, API Gateway, CloudWatch Logs and DynamoDB. Every `Resource`
ends in a name prefix (`function:parking-*`, `role/parking-*`,
`table/parking_*`) so the key can only touch this project's resources —
it cannot create a role called `admin-everything`. The `iam:PassRole`
statement carries a `Condition` limiting it to `lambda.amazonaws.com`,
because "create a role" and "hand a role to a service" are separate
permissions in AWS, and an unrestricted `PassRole` is a privilege
escalation waiting to happen.

Two details worth remembering: IAM ARNs have an empty region slot
(`arn:aws:iam::ACCOUNT:role/...`) because IAM is global, and API Gateway's
actions are HTTP verbs (`apigateway:POST`) rather than named calls.
**What I understand:**
**What I still need to learn:**

---

## A role has two policies

**Why we needed it:** the deployed code needs AWS permissions, but putting
an access key in the source is exactly what the brief forbids.
**What it does:** a role is like a uniform, and it carries two separate
documents. The **trust policy** answers *who may put it on* — its fields
are `Effect`, `Principal` and `Action`, where `Principal` is the "who".
The **permissions policy** answers *what you may do while wearing it* —
the familiar `Effect`, `Action`, `Resource`. A trust policy needs no
`Resource`, because the resource is the role itself.
**How we used it:** `parking-lambda-exec` trusts only
`lambda.amazonaws.com` via `sts:AssumeRole`, and grants four DynamoDB
actions on one table plus writing to its own log group. Lambda assumes it
at runtime and receives temporary credentials — no key exists anywhere.
**What I understand:**
**What I still need to learn:**

---

## Identity-based vs resource-based policies

**Why we needed it:** API Gateway had to be allowed to invoke the Lambda
function, and none of the policies written so far could express that.
**What it does:** two directions to the same lock. An **identity-based**
policy is attached to a user or role and says *"this identity may do these
things."* A **resource-based** policy is attached to the thing itself and
says *"these callers may touch me."* Some permissions can only be granted
from one side.
**How we used it:** `aws_lambda_permission` attaches a resource-based
policy to the function, naming `apigateway.amazonaws.com` as the allowed
principal and restricting it by `source_arn` to this specific API. This is
also why the deployment policy needed `lambda:AddPermission`,
`lambda:RemovePermission` and `lambda:GetPolicy` — those three actions
exist to manage a function's resource-based policy.
**What I understand:**
**What I still need to learn:**

---

## Packaging code for Lambda, and why `build/` is dangerous

**Why we needed it:** Lambda runs a zip file, not a folder on my laptop,
and the Python runtime only ships boto3 — FastAPI, Mangum and Pydantic
have to be bundled.
**What it does:** two ideas, both of which bit us.

First, **you are building for a different machine.** Pydantic contains
compiled code, and `pip` normally downloads builds for the machine it is
running on — arm64 macOS. Lambda is x86-64 Linux.
`--platform manylinux2014_x86_64 --only-binary=:all:` forces the Linux
builds. The proof is in the filename:
`_pydantic_core.cpython-313-x86_64-linux-gnu.so`. Get it wrong and it
uploads happily, then fails at runtime with an unhelpful import error.

Second, **`build/` is a snapshot, not a link.** `cp -r app build/` copies
the code at one moment. Editing `app/` afterwards changes nothing in
`build/`. We hit exactly this: local tests passed against `app/` while the
zip still held the old buggy `PUT`. Testing one version and shipping
another, with nothing warning us.
**How we used it:** `requirements-lambda.txt` lists only runtime
dependencies, the build starts with `rm -rf build` so stale files cannot
survive, and the build must be re-run after any change to `app/`.
**What I understand:**
**What I still need to learn:**

---

## Terraform: data sources, outputs, and dependencies

**Why we needed it:** the zip had to be created, the URL had to be
findable, and some things must happen in a specific order.
**What it does:**
- A **`data` block** reads or computes something Terraform does not own.
  `archive_file` produces a zip on local disk — no AWS object involved.
  Data sources resolve during `plan`, which is why the zip's hash was
  already known before `apply` ran.
- An **`output`** hands a value back after apply. `terraform output
  api_url` prints the URL rather than hunting for it in the console.
- **Dependencies** are normally free: referencing
  `aws_dynamodb_table.parking_spots.arn` tells Terraform the table must
  exist first. Order is never declared, it is inferred from references.
  **`depends_on`** is the escape hatch for when there is no reference —
  the Lambda function doesn't mention the log group, so without it Lambda
  could create its own retention-less group first.
**How we used it:** all three, plus `path.module` to keep paths relative
to the config folder rather than hardcoded to this laptop.
**What I understand:**
**What I still need to learn:**

---

## Tainted resources, and reading a destroy count

**Why we needed it:** a `plan` showed `1 to destroy` when nothing should
have been destroyed, which is exactly the moment the habit matters.
**What it does:** when Terraform creates something but then fails before
it can confirm the result, it marks the resource **tainted** — "I made
this, but I don't trust it." The next plan shows `-/+`, meaning destroy
then recreate. Three symbols in total: `+` create, `~` modify in place,
`-` destroy.
**How we used it:** the log group was created, then the read-back was
denied, so it came back tainted and was rebuilt on the next run. The rule
that came out of it is better than the one I started with: **never approve
a destroy you cannot explain** — not "never approve a destroy." Here the
reason was printed on screen and the thing being destroyed was empty.
**What I understand:**
**What I still need to learn:**

---

## List operations cannot be scoped to a resource

**Why we needed it:** the first `apply` of the log group failed with
`AccessDenied` on `logs:DescribeLogGroups`, despite the policy granting
log permissions on `/aws/lambda/parking-*`.
**What it does:** the error named the resource it evaluated against —
`log-group::log-stream:`, with the group name slot **empty**. That is the
explanation. `DescribeLogGroups` asks *which groups exist*, a question
that names no particular group, so no prefix pattern can match it. List
and describe operations generally need `Resource: "*"`.
**How we used it:** rather than widening the whole statement, the single
list action was isolated into its own statement on `"*"`, leaving the six
scopeable log actions restricted. Recorded as a documented exception in
`ARCHITECTURE.md` rather than a doc that quietly claims perfect scoping.
**What I understand:**
**What I still need to learn:**
