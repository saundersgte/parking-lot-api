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
**What I understand:**
**What I still need to learn:**

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
**What I understand:**
**What I still need to learn:**

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
**What I understand:**
**What I still need to learn:**

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
**What I understand:**
**What I still need to learn:**
