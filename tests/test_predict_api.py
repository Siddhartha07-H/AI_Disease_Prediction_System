"""
Integration tests for FastAPI endpoints
"""

from fastapi.testclient import TestClient
from backend.main import app
from backend.auth import create_access_token

client = TestClient(app)


def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["features_count"] == 132


def test_symptoms_endpoint():
    response = client.get("/symptoms")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 132
    assert len(data["detailed"]) == 132
    assert "itching" in data["symptoms"]


def test_predict_unauthenticated():
    response = client.post("/predict", json={"symptoms": ["itching", "skin_rash", "fatigue"]})
    assert response.status_code == 401


def test_predict_authenticated_success():
    token = create_access_token(user_id=1, role="patient")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"symptoms": ["itching", "skin_rash", "nodal_skin_eruptions"]}
    response = client.post("/predict", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "confidence" in data
    assert "differential_diagnoses" in data
    assert "precautions" in data
    assert "specialist" in data
    assert len(data["precautions"]) > 0


def test_predict_minimum_symptom_guard():
    token = create_access_token(user_id=1, role="patient")
    headers = {"Authorization": f"Bearer {token}"}

    # Only 2 symptoms - must trigger 422 safeguard
    payload = {"symptoms": ["itching", "skin_rash"]}
    response = client.post("/predict", json=payload, headers=headers)

    assert response.status_code == 422
    data = response.json()
    assert "at least 3 symptoms" in str(data["detail"]).lower()


def test_predict_unknown_symptom():
    token = create_access_token(user_id=1, role="patient")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"symptoms": ["fake_nonexistent_symptom_xyz", "itching", "skin_rash"]}
    response = client.post("/predict", json=payload, headers=headers)

    assert response.status_code == 400


def test_disease_info_endpoint():
    response = client.get("/disease-info/GERD")
    assert response.status_code == 200
    data = response.json()
    assert "specialist" in data
    assert "precautions" in data


def test_doctors_endpoint():
    response = client.get("/doctors")
    assert response.status_code == 200
    data = response.json()
    assert "doctors" in data
    assert len(data["doctors"]) > 0


def test_health_tips_endpoint():
    response = client.get("/health-tips")
    assert response.status_code == 200
    data = response.json()
    assert "tips" in data
    assert len(data["tips"]) > 0
