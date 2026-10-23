
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.auth import router as auth_router
from backend.database import (
    book_appointment,
    cancel_appointment,
    get_doctors,
    get_health_tips,
    get_prediction_by_id,
    get_prediction_history,
    get_user_appointments,
    get_user_profile,
    save_prediction,
    save_user_profile,
)
from backend.security import get_current_user

# -------------------------------------------------------------
# Configuration & Paths
# -------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
load_dotenv(ROOT_DIR / ".env")

MODEL_NAME = os.getenv("AI_MODEL_NAME", "disease_model.pkl")
ALLOWED_MODELS = {
    "disease_model.pkl",
    "random_forest_candidate.pkl",
}

if MODEL_NAME not in ALLOWED_MODELS:
    raise ValueError(f"Unsupported model filename: {MODEL_NAME}")

MODEL_PATH = ROOT_DIR / "ai_model" / MODEL_NAME
TRAIN_PATH = ROOT_DIR / "datasets" / "Training.csv"
DISEASE_INFO_PATH = ROOT_DIR / "database" / "disease_info.json"

# Load Clinical Factsheet Knowledge Base
DISEASE_INFO: Dict[str, Dict[str, Any]] = {}
if DISEASE_INFO_PATH.exists():
    with open(DISEASE_INFO_PATH, "r", encoding="utf-8") as f:
        DISEASE_INFO = json.load(f)

# Load AI Model
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

if not TRAIN_PATH.exists():
    raise FileNotFoundError(f"Training dataset not found: {TRAIN_PATH}")

model = joblib.load(MODEL_PATH)

train = pd.read_csv(TRAIN_PATH)
train = train.loc[:, ~train.columns.astype(str).str.startswith("Unnamed")]

if "prognosis" not in train.columns:
    raise ValueError("The training dataset must contain prognosis.")

symptoms = train.drop(columns=["prognosis"]).columns.tolist()
model_features = list(model.feature_names_in_)

if len(model_features) != len(symptoms) or set(model_features) != set(symptoms):
    raise ValueError("Model features do not match dataset symptom columns.")


# -------------------------------------------------------------
# Categorize Symptoms for Polished UI Grouping
# -------------------------------------------------------------
def categorize_symptom(sym: str) -> str:
    s = sym.lower()
    if any(k in s for k in ["skin", "itch", "rash", "eruption", "blister", "pimples", "nails", "scurring", "peeling"]):
        return "Skin & Hair"
    if any(k in s for k in ["stomach", "acidity", "vomit", "diarrhoea", "constipat", "abdominal", "belly", "digest", "ulcer"]):
        return "Gastrointestinal"
    if any(k in s for k in ["cough", "breath", "sneez", "phlegm", "sputum", "throat", "sinus", "chest_pain"]):
        return "Respiratory & Chest"
    if any(k in s for k in ["headache", "dizz", "sensorium", "paralysis", "slurred_speech", "balance", "spinning", "unstead"]):
        return "Neurological"
    if any(k in s for k in ["joint", "knee", "hip", "neck", "back_pain", "muscle", "stiff", "cramps"]):
        return "Musculoskeletal"
    if any(k in s for k in ["urine", "micturition", "bladder", "polyuria"]):
        return "Urinary & Renal"
    if any(k in s for k in ["fever", "chills", "sweat", "fatigue", "lethargy", "weight", "malaise"]):
        return "General & Systemic"
    return "Other Symptoms"


SYMPTOM_METADATA = [
    {
        "id": sym,
        "name": sym.replace("_", " ").title(),
        "category": categorize_symptom(sym),
    }
    for sym in symptoms
]

# Emergency symptom triggers
EMERGENCY_SYMPTOMS = {
    "chest_pain",
    "breathlessness",
    "weakness_of_one_body_side",
    "slurred_speech",
    "coma",
    "altered_sensorium",
    "stomach_bleeding",
    "blood_in_sputum",
    "loss_of_balance",
}


# -------------------------------------------------------------
# FastAPI App Initialization
# -------------------------------------------------------------
app = FastAPI(
    title="HealthAI - Disease Prediction & Clinical Management API",
    description="Production-grade AI disease prediction, appointment booking, and patient records system.",
    version="2.0.0",
)

# CORS: Permissive for Web browsers, PWA, and Android WebView
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Authentication Router
app.include_router(auth_router)


# -------------------------------------------------------------
# Pydantic Request Models
# -------------------------------------------------------------
class SymptomInput(BaseModel):
    symptoms: List[str] = Field(min_length=1, max_length=len(symptoms))


class AppointmentInput(BaseModel):
    doctor_id: Optional[int] = None
    doctor_name: str = Field(min_length=2, max_length=150)
    specialty: str = Field(min_length=2, max_length=150)
    appointment_date: str
    time_slot: str
    reason: Optional[str] = None


class ProfileInput(BaseModel):
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = Field(None, max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = Field(None, max_length=30)
    emergency_contact: Optional[str] = Field(None, max_length=100)
    allergies: Optional[str] = Field(None, max_length=255)


# -------------------------------------------------------------
# Core API Endpoints
# -------------------------------------------------------------
@app.get("/api/status")
def system_status():
    return {
        "status": "online",
        "service": "HealthAI Disease Prediction Engine",
        "model_type": type(model).__name__,
        "model_file": MODEL_NAME,
        "features_count": len(model_features),
        "classes_count": len(train["prognosis"].unique()),
    }


@app.get("/symptoms")
def get_symptoms():
    """Return all 132 symptoms with display names and category groupings."""
    return {
        "total": len(symptoms),
        "symptoms": symptoms,
        "detailed": SYMPTOM_METADATA,
    }


@app.get("/disease-info/{disease_name}")
def get_disease_details(disease_name: str):
    """Retrieve full clinical factsheet, precautions, and specialist for a disease."""
    # Attempt direct or trimmed match
    info = DISEASE_INFO.get(disease_name) or DISEASE_INFO.get(disease_name.strip())
    if not info:
        # Search case-insensitively
        for k, v in DISEASE_INFO.items():
            if k.strip().lower() == disease_name.strip().lower():
                info = v
                break

    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Clinical information for '{disease_name}' not found.",
        )
    return info


@app.post("/predict")
def predict(
    data: SymptomInput,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate authenticated disease prediction with differential diagnoses,
    confidence metrics, severity rating, and specialist recommendation.
    """
    unknown = [s for s in data.symptoms if s not in symptoms]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail={"error": "Unknown symptoms detected", "symptoms": unknown},
        )

    selected = list(dict.fromkeys(data.symptoms))

    # Require minimum of 3 symptoms as a safety guard
    if len(selected) < 3:
        raise HTTPException(
            status_code=422,
            detail=(
                "Please select at least 3 symptoms to generate a reliable AI assessment. "
                "This software safeguard prevents unreliable single-symptom extrapolations."
            ),
        )

    # Check for critical emergency symptoms
    detected_emergencies = [s.replace("_", " ").title() for s in selected if s in EMERGENCY_SYMPTOMS]
    has_emergency_symptoms = len(detected_emergencies) > 0

    # Build input vector exactly matching model features
    input_vector = pd.DataFrame(
        [[1 if s in selected else 0 for s in model_features]],
        columns=model_features,
    )

    try:
        raw_prediction = str(model.predict(input_vector)[0])
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"The AI model failed to generate a prediction: {exc}",
        )

    # Compute confidence and top 3 differential candidates
    top_candidates = []
    confidence = 85.0

    if hasattr(model, "predict_proba"):
        try:
            probabilities = model.predict_proba(input_vector)[0]
            classes = model.classes_
            sorted_indices = np.argsort(probabilities)[::-1]

            top_prob = float(probabilities[sorted_indices[0]])
            confidence = round(max(top_prob * 100.0, 50.0), 1)

            for idx in sorted_indices[:3]:
                c_name = str(classes[idx])
                c_info = DISEASE_INFO.get(c_name) or DISEASE_INFO.get(c_name.strip()) or {}
                prob_val = round(float(probabilities[idx]) * 100.0, 1)
                if prob_val > 0.0:
                    top_candidates.append({
                        "disease": c_name.strip(),
                        "display_name": c_info.get("display_name", c_name.strip()),
                        "probability": prob_val,
                    })
        except Exception:
            confidence = 85.0

    # Fetch clinical metadata for predicted disease
    disease_meta = DISEASE_INFO.get(raw_prediction) or DISEASE_INFO.get(raw_prediction.strip()) or {}
    display_title = disease_meta.get("display_name", raw_prediction.strip())
    specialist = disease_meta.get("specialist", "General Physician")
    severity = disease_meta.get("severity", "Moderate")
    is_critical = disease_meta.get("is_emergency", False) or has_emergency_symptoms

    precautions = disease_meta.get("precautions", [
        "Consult a qualified physician for an accurate diagnostic evaluation",
        "Monitor symptoms and avoid strenuous activities",
        "Keep a detailed daily log of symptoms and food intake",
        "Stay hydrated and maintain proper rest",
    ])

    medications = disease_meta.get("medications", [
        "Symptomatic relief as advised by a licensed practitioner",
        "Do not self-medicate with unprescribed pharmaceuticals",
    ])

    diet_advice = disease_meta.get("diet_advice", "Balanced, nutrient-rich diet with adequate hydration.")

    # Save prediction in database
    inserted_id = None
    try:
        inserted_id = save_prediction(
            symptoms=selected,
            prediction=raw_prediction.strip(),
            user_id=current_user["id"],
            confidence=confidence,
            severity="Critical" if is_critical else severity,
            doctor_recommendation=specialist,
        )
    except Exception as exc:
        print(f"Warning: Failed to save prediction to database: {exc}")

    return {
        "id": inserted_id,
        "prediction": raw_prediction.strip(),
        "display_name": display_title,
        "confidence": confidence,
        "severity": "Critical" if is_critical else severity,
        "is_emergency": is_critical,
        "emergency_symptoms_detected": detected_emergencies,
        "specialist": specialist,
        "precautions": precautions,
        "medications": medications,
        "diet_advice": diet_advice,
        "differential_diagnoses": top_candidates,
        "status": "Doctor Review Required",
        "disclaimer": (
            "NOTICE: HealthAI provides unverified machine-learning decision support. "
            "This result is NOT a clinical diagnosis or medical prescription. "
            "Always consult a licensed medical professional before taking any health action."
        ),
    }


# -------------------------------------------------------------
# Prediction History & Medical Report Endpoints
# -------------------------------------------------------------
@app.get("/history")
def prediction_history(current_user: dict = Depends(get_current_user)):
    """Retrieve full prediction history for the authenticated patient."""
    history = get_prediction_history(current_user["id"])
    return {
        "total": len(history),
        "history": history,
    }


@app.get("/history/{prediction_id}/report")
def get_medical_report(prediction_id: int, current_user: dict = Depends(get_current_user)):
    """Generate structured printable medical report data for a specific prediction."""
    record = get_prediction_by_id(prediction_id, current_user["id"])
    if not record:
        raise HTTPException(status_code=404, detail="Prediction record not found.")

    profile = get_user_profile(current_user["id"])
    disease_name = record["prediction"]
    disease_meta = DISEASE_INFO.get(disease_name) or DISEASE_INFO.get(disease_name.strip()) or {}

    return {
        "report_id": f"HAI-REP-{record['id']:06d}",
        "generated_at": record["created_at"],
        "patient": {
            "id": current_user["id"],
            "name": profile.get("full_name", "Patient"),
            "email": profile.get("email"),
            "age": profile.get("age", "N/A"),
            "gender": profile.get("gender", "N/A"),
            "blood_group": profile.get("blood_group", "N/A"),
            "emergency_contact": profile.get("emergency_contact", "N/A"),
        },
        "diagnosis_data": {
            "prediction": record["prediction"],
            "display_name": disease_meta.get("display_name", record["prediction"]),
            "confidence": record.get("confidence", 85.0),
            "severity": record.get("severity", "Moderate"),
            "specialist": record.get("doctor_recommendation", "General Physician"),
            "symptoms_reported": [s.strip().replace("_", " ").title() for s in record["symptoms"].split(",")],
            "precautions": disease_meta.get("precautions", []),
            "medications": disease_meta.get("medications", []),
            "diet_advice": disease_meta.get("diet_advice", ""),
        },
        "disclaimer": (
            "This report is generated by HealthAI clinical decision-support software for informational purposes. "
            "It does not constitute a legally binding medical diagnosis. Please present this report to your physician."
        ),
    }


# -------------------------------------------------------------
# Patient Profile Endpoints
# -------------------------------------------------------------
@app.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    """Fetch patient profile details."""
    profile = get_user_profile(current_user["id"])
    return profile


@app.put("/profile")
def update_profile(data: ProfileInput, current_user: dict = Depends(get_current_user)):
    """Update patient health profile."""
    save_user_profile(current_user["id"], data.model_dump())
    return {"message": "Profile updated successfully.", "profile": get_user_profile(current_user["id"])}


# -------------------------------------------------------------
# Doctor Appointments Endpoints
# -------------------------------------------------------------
@app.get("/doctors")
def list_doctors():
    """List all available verified doctors and specialists."""
    return {"doctors": get_doctors()}


@app.get("/appointments")
def list_appointments(current_user: dict = Depends(get_current_user)):
    """List appointments for the authenticated patient."""
    appointments = get_user_appointments(current_user["id"])
    return {"total": len(appointments), "appointments": appointments}


@app.post("/appointments", status_code=status.HTTP_201_CREATED)
def create_appointment(data: AppointmentInput, current_user: dict = Depends(get_current_user)):
    """Book a new doctor appointment."""
    new_apt = book_appointment(
        user_id=current_user["id"],
        doctor_id=data.doctor_id,
        doctor_name=data.doctor_name,
        specialty=data.specialty,
        appointment_date=data.appointment_date,
        time_slot=data.time_slot,
        reason=data.reason,
    )
    return {"message": "Appointment confirmed successfully.", "appointment": new_apt}


@app.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: int, current_user: dict = Depends(get_current_user)):
    """Cancel an appointment."""
    cancelled = cancel_appointment(appointment_id, current_user["id"])
    if not cancelled:
        raise HTTPException(status_code=404, detail="Appointment not found or already cancelled.")
    return {"message": "Appointment cancelled successfully."}


# -------------------------------------------------------------
# Curated Health Tips Endpoint
# -------------------------------------------------------------
@app.get("/health-tips")
def list_health_tips():
    """Fetch curated preventive healthcare tips."""
    return {"tips": get_health_tips()}


# -------------------------------------------------------------
# Serve Static Frontend Files & Web App
# -------------------------------------------------------------
if FRONTEND_DIR.exists():
    @app.get("/login")
    def serve_login():
        return FileResponse(FRONTEND_DIR / "login.html")

    @app.get("/register")
    def serve_register():
        return FileResponse(FRONTEND_DIR / "register.html")

    @app.get("/predict-page")
    def serve_predict_page():
        return FileResponse(FRONTEND_DIR / "predict.html")

    @app.get("/privacy")
    def serve_privacy():
        return FileResponse(FRONTEND_DIR / "privacy.html")

    @app.get("/terms")
    def serve_terms():
        return FileResponse(FRONTEND_DIR / "terms.html")

    # Mount /static for explicit asset links
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    # Mount entire frontend at root (serves index.html at /, style.css, script.js, *.html)
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

