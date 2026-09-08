import pytest

from app import storage


@pytest.fixture(autouse=True)
def clean_table():
    yield
    for spot in storage.list_spots():
        storage.delete_spot(spot.spot_id)
        