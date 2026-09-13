from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_spot():
    response = client.post("/spots", json={"spot_id": "T1", "status": "AVAILABLE"})
    assert response.status_code == 201
    assert response.json() == {"spot_id": "T1", "status": "AVAILABLE"}

def test_get_spot():
    client.post("/spots", json={"spot_id": "T2", "status": "AVAILABLE"})
    response = client.get("/spots/T2")
    assert response.status_code == 200
    assert response.json()["spot_id"] == "T2"

def test_get_spot_not_found():
    response = client.get("/spots/NOPE")
    assert response.status_code == 404

def test_check_in_and_out():
    client.post("/spots", json={"spot_id": "T3", "status": "AVAILABLE"})

    response = client.post("/spots/T3/check-in")
    assert response.status_code == 200
    assert response.json()["status"] == "OCCUPIED"

    response = client.post("/spots/T3/check-out")
    assert response.status_code == 200
    assert response.json()["status"] == "AVAILABLE"

def test_check_in_twice_conflicts():
    client.post("/spots", json={"spot_id": "T4", "status": "AVAILABLE"})
    client.post("/spots/T4/check-in")

    response = client.post("/spots/T4/check-in")
    assert response.status_code == 409

def test_put_mismatched_id_rejected():
    client.post("/spots", json={"spot_id": "T5", "status": "AVAILABLE"})

    response = client.put("/spots/T5", json={"spot_id": "T6", "status": "OCCUPIED"})
    assert response.status_code == 400