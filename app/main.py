"""Parking Lot API - application entry point.

Run locally from the project root with:

    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

# `app` is the application object.
#
# It is the single thing a web server needs in order to run this API.
# Locally, uvicorn picks it up. In AWS, Mangum will hand it the Lambda
# event instead. The application code below does not know or care which
# of those is happening - that is the whole point of this design.
app = FastAPI(
    title="Parking Lot API",
    version="0.1.0",
)


# =====================================================================
# YOUR TASK - write the health check endpoint below this comment.
#
# Requirement:
#     GET /health   ->   {"status": "ok"}
#
# Hints (Level 1 - a clue, not the answer):
#
#   * A route is an ordinary Python function with a decorator on the
#     line directly above it.
#
#   * The decorator you need is  @app.get("/health")
#     Read it as: "when a GET request arrives for /health, run the
#     function underneath me."
#
#   * The function needs no parameters. Give it a sensible name -
#     the name is for you, not for the URL. The URL comes from the
#     decorator.
#
#   * Whatever the function RETURNS becomes the response body.
#     Return a Python dictionary and FastAPI converts it to JSON
#     automatically. You do not need to import json, or call
#     json.dumps, or build a Response object.
#
# Delete this comment block once it works.
# =====================================================================
