"""Parking Lot API - application entry point.

Run locally from the project root with:

    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi import HTTPException
from app.models import Spot
from app import storage

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

@app.post("/spots", status_code=201)
def create_spot(spot: Spot):
    storage.save_spot(spot)
    return spot

@app.get("/spots")
def get_spots():
    return storage.list_spots()

@app.get("/spots/{spot_id}")
def get_spot(spot_id: str):
    spot = storage.get_spot(spot_id)
    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")
    return spot