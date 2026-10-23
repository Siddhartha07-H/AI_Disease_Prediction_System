import uuid
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_doctor_registration_and_login():
    unique_email = f"dr.test_{uuid.uuid4().hex[:8]}@hospital.org"

    # Register Doctor
    reg_response = client.post(
        "/doctor/register",
        json={
            "full_name": "Dr. Alexander Wright",
            "email": unique_email,
            "password": "SecureDoctorPassword123!",
            "specialty": "Cardiologist",
            "experience_years": 12,
            "clinic_address": "Pavilion Heart Hospital, Suite 500",
            "contact_phone": "+1 (800) 555-9988",
            "license_number": "MED-REG-884920",
        },
    )
    assert reg_response.status_code == 201, reg_response.text
    data = reg_response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "doctor"
    assert data["doctor"]["specialty"] == "Cardiologist"
    token = data["access_token"]

    # Login as Doctor
    login_response = client.post(
        "/doctor/login",
        json={
            "email": unique_email,
            "password": "SecureDoctorPassword123!",
        },
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["user"]["role"] == "doctor"
    assert login_data["doctor"]["name"].startswith("Dr.")

    # Access Doctor Dashboard /me
    me_response = client.get(
        "/api/doctor/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert "doctor" in me_data
    assert "stats" in me_data
    assert me_data["doctor"]["specialty"] == "Cardiologist"

    # Access Doctor Appointments
    apts_response = client.get(
        "/api/doctor/appointments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert apts_response.status_code == 200
    assert "appointments" in apts_response.json()


def test_patient_cannot_access_doctor_endpoints():
    unique_email = f"patient_{uuid.uuid4().hex[:8]}@test.com"

    # Register Patient
    client.post(
        "/register",
        json={
            "full_name": "Test Patient",
            "email": unique_email,
            "password": "PatientPassword123!",
        },
    )

    # Login as Patient
    login_res = client.post(
        "/login",
        json={
            "email": unique_email,
            "password": "PatientPassword123!",
        },
    )
    assert login_res.status_code == 200
    patient_token = login_res.json()["access_token"]

    # Attempt to access doctor-only endpoint
    doc_me_res = client.get(
        "/api/doctor/me",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert doc_me_res.status_code == 403
    assert "restricted" in doc_me_res.json()["detail"].lower()
