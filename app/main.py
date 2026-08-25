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

# health check for fastapi
@app.get("/health")
def health_check():
    return {"status": "ok"}

