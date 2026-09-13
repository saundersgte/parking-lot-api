"""Parking Lot API - application entry point.

Run locally from the project root with:

    uvicorn app.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from app.models import Spot
from app import storage
from mangum import Mangum

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

@app.post("/spots/{spot_id}/check-in")
def check_in(spot_id: str):
    spot = storage.get_spot(spot_id)
    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")
    if spot.status != "AVAILABLE":
        raise HTTPException(status_code=409, detail="Spot is not available")
    spot.status = "OCCUPIED"
    storage.save_spot(spot)
    return spot

@app.post("/spots/{spot_id}/check-out")
def check_out(spot_id: str):
    spot = storage.get_spot(spot_id)
    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not found")
    if spot.status != "OCCUPIED":
        raise HTTPException(status_code=409, detail="Spot is not occupied")
    spot.status = "AVAILABLE"
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

@app.put("/spots/{spot_id}")
def update_spot(spot_id: str, spot:Spot):
    if storage.get_spot(spot_id) is None:
        raise HTTPException(status_code=404, detail="Spot not found")
    storage.save_spot(spot)
    return spot

@app.delete("/spots/{spot_id}", status_code=204)
def delete_spot(spot_id: str):
    if storage.get_spot(spot_id) is None:
        raise HTTPException(status_code=404, detail="Spot not found")
    storage.delete_spot(spot_id)

handler = Mangum(app)
