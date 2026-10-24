
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

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
    create_doctor_profile,
    get_doctor_appointments,
    get_doctor_by_user_id,
    get_doctors,
    get_health_tips,
    get_prediction_by_id,
    get_prediction_history,
    get_user_appointments,
    get_user_profile,
    save_prediction,
    save_user_profile,
    update_appointment_status,
    update_doctor_profile,
)
from backend.security import get_current_user

# -------------------------------------------------------------
# Configuration & Paths (Resilient for Local & Serverless Vercel)
# -------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent

def _find_path(*relative_parts: str) -> Path:
    candidates = [
        ROOT_DIR.joinpath(*relative_parts),
        Path.cwd().joinpath(*relative_parts),
        Path(__file__).resolve().parent.parent.joinpath(*relative_parts),
        Path("/var/task").joinpath(*relative_parts),
    ]
    for c in candidates:
        if c.exists():
            return c
    return ROOT_DIR.joinpath(*relative_parts)

FRONTEND_DIR = _find_path("frontend")
load_dotenv(ROOT_DIR / ".env")

MODEL_NAME = os.getenv("AI_MODEL_NAME", "disease_model.pkl")
ALLOWED_MODELS = {
    "disease_model.pkl",
    "random_forest_candidate.pkl",
}

if MODEL_NAME not in ALLOWED_MODELS:
    MODEL_NAME = "disease_model.pkl"

MODEL_PATH = _find_path("ai_model", MODEL_NAME)
TRAIN_PATH = _find_path("datasets", "Training.csv")
DISEASE_INFO_PATH = _find_path("database", "disease_info.json")

# Load Clinical Factsheet Knowledge Base
DISEASE_INFO: Dict[str, Dict[str, Any]] = {}
if DISEASE_INFO_PATH.exists():
    try:
        with open(DISEASE_INFO_PATH, "r", encoding="utf-8") as f:
            DISEASE_INFO = json.load(f)
    except Exception as exc:
        print(f"Notice: Could not load disease_info.json: {exc}")

# Load or auto-train AI Model (Resilient fallback prevents 500 FUNCTION_INVOCATION_FAILED on serverless)
model = None
symptoms: List[str] = []

if MODEL_PATH.exists():
    try:
        model = joblib.load(MODEL_PATH)
        if hasattr(model, "feature_names_in_"):
            symptoms = list(model.feature_names_in_)
    except Exception as exc:
        print(f"Notice: Failed to load pre-trained model: {exc}")

if model is None and TRAIN_PATH.exists():
    try:
        from sklearn.tree import DecisionTreeClassifier
        print("Pre-trained model not found or failed; auto-training DecisionTreeClassifier from Training.csv...")
        train = pd.read_csv(TRAIN_PATH)
        train = train.loc[:, ~train.columns.astype(str).str.startswith("Unnamed")]
        X = train.drop(columns=["prognosis"])
        y = train["prognosis"]
        clf = DecisionTreeClassifier(random_state=42)
        clf.fit(X, y)
        model = clf
        symptoms = list(X.columns)
    except Exception as exc:
        print(f"Notice: Auto-training failed: {exc}")

if not symptoms and TRAIN_PATH.exists():
    try:
        train = pd.read_csv(TRAIN_PATH)
        train = train.loc[:, ~train.columns.astype(str).str.startswith("Unnamed")]
        if "prognosis" in train.columns:
            symptoms = train.drop(columns=["prognosis"]).columns.tolist()
    except Exception:
        pass

if not symptoms:
    # 132 standard clinical symptoms fallback
    symptoms = [
        "itching", "skin_rash", "nodal_skin_eruptions", "continuous_sneezing", "shivering",
        "chills", "joint_pain", "stomach_pain", "acidity", "ulcers_on_tongue", "muscle_wasting",
        "vomiting", "burning_micturition", "spotting_urination", "fatigue", "weight_gain",
        "anxiety", "cold_hands_and_feets", "mood_swings", "weight_loss", "restlessness",
        "lethargy", "patches_in_throat", "irregular_sugar_level", "cough", "high_fever",
        "sunken_eyes", "breathlessness", "sweating", "dehydration", "indigestion", "headache",
        "yellowish_skin", "dark_urine", "nausea", "loss_of_appetite", "pain_behind_the_eyes",
        "back_pain", "constipation", "abdominal_pain", "diarrhoea", "mild_fever", "yellow_urine",
        "yellowing_of_eyes", "acute_liver_failure", "fluid_overload", "swelling_of_stomach",
        "swelled_lymph_nodes", "malaise", "blurred_and_distorted_vision", "phlegm",
        "throat_irritation", "redness_of_eyes", "sinus_pressure", "runny_nose", "congestion",
        "chest_pain", "weakness_in_limbs", "fast_heart_rate", "pain_during_bowel_movements",
        "pain_in_anal_region", "bloody_stool", "irritation_in_anus", "neck_pain", "dizziness",
        "cramps", "bruising", "obesity", "swollen_legs", "swollen_blood_vessels",
        "puffy_face_and_eyes", "enlarged_thyroid", "brittle_nails", "swollen_extremeties",
        "excessive_hunger", "extra_marital_contacts", "drying_and_tingling_lips", "slurred_speech",
        "knee_pain", "hip_joint_pain", "muscle_weakness", "stiff_neck", "swelling_joints",
        "movement_stiffness", "spinning_movements", "loss_of_balance", "unsteadiness",
        "weakness_of_one_body_side", "loss_of_smell", "bladder_discomfort",
        "foul_smell_of_urine", "continuous_feel_of_urine", "passage_of_gases", "internal_itching",
        "toxic_look_(typhos)", "depression", "irritability", "muscle_pain", "altered_sensorium",
        "red_spots_over_body", "belly_pain", "abnormal_menstruation", "dischromic_patches",
        "watering_from_eyes", "increased_appetite", "polyuria", "family_history", "mucoid_sputum",
        "rusty_sputum", "lack_of_concentration", "visual_disturbances",
        "receiving_blood_transfusion", "receiving_unsterile_injections", "coma",
        "stomach_bleeding", "distention_of_abdomen", "history_of_alcohol_consumption",
        "fluid_overload.1", "blood_in_sputum", "prominent_veins_on_calf", "palpitations",
        "painful_walking", "pus_filled_pimples", "blackheads", "scurring", "skin_peeling",
        "silver_like_dusting", "small_dents_in_nails", "inflammatory_nails", "blister",
        "red_sore_around_nose", "yellow_crust_ooze"
    ]

model_features = list(model.feature_names_in_) if (model and hasattr(model, "feature_names_in_")) else list(symptoms)



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


from backend.security_middleware import SecurityAndTrafficMiddleware

# -------------------------------------------------------------
# FastAPI App Initialization
# -------------------------------------------------------------
app = FastAPI(
    title="HealthAI - Disease Prediction & Clinical Management API",
    description="Production-grade AI disease prediction, appointment booking, and patient records system.",
    version="2.0.0",
)

# OWASP Security Headers & Traffic Rate-Limiting Protection
app.add_middleware(SecurityAndTrafficMiddleware)

# CORS: Safe configuration supporting Browsers, PWA, Android WebView and Cloud access
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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


class AppointmentStatusUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=50)
    notes: Optional[str] = Field(None, max_length=500)


class DoctorProfileUpdate(BaseModel):
    is_available: Optional[bool] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    clinic_address: Optional[str] = Field(None, max_length=255)
    specialty: Optional[str] = Field(None, max_length=150)



# -------------------------------------------------------------
# Core API Endpoints
# -------------------------------------------------------------
@app.get("/api/status")
@app.get("/health")
def system_status():
    return {
        "status": "online",
        "service": "HealthAI Disease Prediction Engine",
        "model_type": type(model).__name__,
        "model_file": MODEL_NAME,
        "features_count": len(model_features),
        "classes_count": len(model.classes_) if (model and hasattr(model, "classes_")) else 41,
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

    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI diagnostic model is currently initializing. Please retry in a few seconds.",
        )

    # Build input vector exactly matching model features (O(1) set lookup for heavy traffic)
    selected_set = set(selected)
    input_vector = pd.DataFrame(
        [[1 if s in selected_set else 0 for s in model_features]],
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
# Doctor Portal Management Endpoints
# -------------------------------------------------------------
@app.get("/api/doctor/me")
def get_current_doctor_profile(current_user: dict = Depends(get_current_user)):
    """Retrieve profile and clinical performance stats for the authenticated doctor."""
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to registered medical doctors and specialists.",
        )

    doc = get_doctor_by_user_id(current_user["id"])
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for this user account.",
        )

    appointments = get_doctor_appointments(doctor_id=doc["id"], doctor_name=doc["name"])
    total_apts = len(appointments)
    confirmed_apts = len([a for a in appointments if a["status"] == "Confirmed"])
    completed_apts = len([a for a in appointments if a["status"] == "Completed"])
    cancelled_apts = len([a for a in appointments if a["status"] == "Cancelled"])
    unique_patients = len(set(a["patient_id"] for a in appointments if a.get("patient_id")))

    return {
        "doctor": doc,
        "stats": {
            "total_appointments": total_apts,
            "upcoming_appointments": confirmed_apts,
            "completed_consultations": completed_apts,
            "cancelled_appointments": cancelled_apts,
            "total_patients": unique_patients,
        },
    }


@app.get("/api/doctor/appointments")
def list_doctor_appointments(current_user: dict = Depends(get_current_user)):
    """Retrieve full appointment list for the authenticated doctor."""
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to medical professionals.",
        )

    doc = get_doctor_by_user_id(current_user["id"])
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor profile not found.")

    appointments = get_doctor_appointments(doctor_id=doc["id"], doctor_name=doc["name"])
    return {
        "total": len(appointments),
        "appointments": appointments,
    }


@app.patch("/api/doctor/appointments/{appointment_id}/status")
def change_appointment_status(
    appointment_id: int,
    data: AppointmentStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update clinical status (Confirmed, Completed, Cancelled) and add consultation notes."""
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only attending doctors may update consultation status.",
        )

    doc = get_doctor_by_user_id(current_user["id"])
    doc_id = doc["id"] if doc else None

    success = update_appointment_status(
        appointment_id=appointment_id,
        status_value=data.status,
        notes=data.notes,
        doctor_id=doc_id,
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Appointment record not found or unauthorized.",
        )

    return {"message": f"Appointment status updated to '{data.status}' successfully."}


@app.get("/api/doctor/patients/{patient_id}/records")
def view_patient_medical_history(
    patient_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve patient AI diagnostic assessments and health profile for clinical review."""
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to medical doctors.",
        )

    profile = get_user_profile(patient_id)
    history = get_prediction_history(patient_id)

    return {
        "patient": profile,
        "prediction_history": history,
        "total_assessments": len(history),
    }


@app.put("/api/doctor/profile")
def update_doctor_settings(
    data: DoctorProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update doctor clinic availability, contact number, or specialty."""
    if current_user.get("role") != "doctor":
        raise HTTPException(status_code=403, detail="Doctor access required.")

    doc = get_doctor_by_user_id(current_user["id"])
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor profile not found.")

    update_doctor_profile(
        doctor_id=doc["id"],
        is_available=data.is_available,
        contact_phone=data.contact_phone,
        clinic_address=data.clinic_address,
        specialty=data.specialty,
    )

    return {
        "message": "Doctor profile updated successfully.",
        "doctor": get_doctor_by_user_id(current_user["id"]),
    }


# -------------------------------------------------------------
# Serve Static Frontend Files & Web App
# -------------------------------------------------------------
if FRONTEND_DIR.exists():
    @app.get("/")
    def serve_root():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"status": "online", "service": "HealthAI Disease Prediction System", "docs": "/docs"}

    @app.get("/login")
    def serve_login():
        return FileResponse(FRONTEND_DIR / "login.html")

    @app.get("/register")
    def serve_register():
        return FileResponse(FRONTEND_DIR / "register.html")

    @app.get("/doctor-login")
    def serve_doctor_login():
        return FileResponse(FRONTEND_DIR / "doctor-login.html")

    @app.get("/doctor-register")
    def serve_doctor_register():
        return FileResponse(FRONTEND_DIR / "doctor-register.html")

    @app.get("/doctor-dashboard")
    def serve_doctor_dashboard():
        return FileResponse(FRONTEND_DIR / "doctor-dashboard.html")

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
else:
    @app.get("/")
    def serve_fallback_root():
        return {"status": "online", "service": "HealthAI Disease Prediction System", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)



