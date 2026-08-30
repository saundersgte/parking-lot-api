from app.models import Spot

_spots: dict[str, Spot] = {}


def save_spot(spot: Spot) -> None:
    _spots[spot.spot_id] = spot

def get_spot(spot_id: str) -> Spot | None:
    return _spots.get(spot_id)


def list_spots() -> list[Spot]:
    return list(_spots.values())

def delete_spot(spot_id: str) -> None:
    del _spots[spot_id]

