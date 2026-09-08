import os

import boto3

from app.models import Spot

TABLE_NAME = os.environ.get("SPOTS_TABLE", "parking_spots")

_table = boto3.resource("dynamodb").Table(TABLE_NAME)

def save_spot(spot: Spot) -> None:
    _table.put_item(Item=spot.model_dump())

def get_spot(spot_id: str) -> Spot | None:
    response = _table.get_item(Key={"spot_id": spot_id})
    item = response.get("Item")
    if item is None:
        return None
    return Spot(**item)
    
def list_spots() -> list[Spot]:
    response = _table.scan()
    return [Spot(**item) for item in response["Items"]]

def delete_spot(spot_id: str) -> None:
    _table.delete_item(Key={"spot_id": spot_id})
    

