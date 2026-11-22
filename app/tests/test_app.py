import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import app as service


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def client():
    return service.app.test_client()


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 418
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["model_version"] == "diabetes-linear-v1"


def test_predict_without_features(client):
    response = client.post("/predict", json={})

    assert response.status_code == 400


def test_predict_wrong_number_of_features(client):
    response = client.post("/predict", json={"features": [1, 2]})

    assert response.status_code == 400


def test_predict_valid_diabetes_request(client, monkeypatch):
    connection = MagicMock()
    monkeypatch.setattr(service, "get_db", lambda: connection)

    request_file = ROOT / "model" / "request1.json"
    payload = json.loads(request_file.read_text(encoding="utf-8"))
    assert len(payload["features"]) == 10

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.get_json()
    assert isinstance(body["prediction"], (int, float))
    assert body["model_version"] == "diabetes-linear-v1"
    assert connection.cursor.called
