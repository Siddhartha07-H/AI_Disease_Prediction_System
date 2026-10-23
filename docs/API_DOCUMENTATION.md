# HealthAI REST API Documentation
## Version: 2.0.0

Base URL: `http://localhost:8000` (or your deployed server domain)

---

## 1. Authentication Endpoints

### 1.1 Register Patient
- **Endpoint:** `POST /register`
- **Status:** `201 Created`
- **Request Body:**
```json
{
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "password": "SecurePassword123"
}
```
- **Response:**
```json
{
  "message": "Patient registered successfully.",
  "user": {
    "id": 1,
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "role": "patient",
    "created_at": "2026-10-22T12:00:00"
  }
}
```

### 1.2 Patient Login
- **Endpoint:** `POST /login`
- **Status:** `200 OK`
- **Request Body:**
```json
{
  "email": "jane@example.com",
  "password": "SecurePassword123"
}
```
- **Response:**
```json
{
  "message": "Login successful.",
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "role": "patient"
  }
}
```

---

## 2. Clinical Symptom & Prediction Endpoints

### 2.1 Get Available Symptoms
- **Endpoint:** `GET /symptoms`
- **Response:**
```json
{
  "total": 132,
  "symptoms": ["itching", "skin_rash", "..."],
  "detailed": [
    {
      "id": "itching",
      "name": "Itching",
      "category": "Skin & Hair"
    }
  ]
}
```

### 2.2 Predict Disease
- **Endpoint:** `POST /predict`
- **Headers:** `Authorization: Bearer <TOKEN>`
- **Request Body:**
```json
{
  "symptoms": ["itching", "skin_rash", "nodal_skin_eruptions"]
}
```
- **Response:**
```json
{
  "id": 42,
  "prediction": "Fungal infection",
  "display_name": "Fungal Skin Infection",
  "confidence": 88.5,
  "severity": "Low",
  "is_emergency": false,
  "emergency_symptoms_detected": [],
  "specialist": "Dermatologist",
  "precautions": [
    "Keep affected skin areas clean, cool, and completely dry",
    "Wear breathable cotton clothing"
  ],
  "medications": [
    "Topical clotrimazole cream",
    "Antifungal dusting powder"
  ],
  "differential_diagnoses": [
    { "disease": "Fungal infection", "display_name": "Fungal Skin Infection", "probability": 88.5 },
    { "disease": "Allergy", "display_name": "Allergic Reaction", "probability": 7.2 }
  ],
  "status": "Doctor Review Required",
  "disclaimer": "HealthAI provides unverified decision support..."
}
```

---

## 3. History & Reports Endpoints

### 3.1 Get Prediction History
- **Endpoint:** `GET /history`
- **Headers:** `Authorization: Bearer <TOKEN>`
- **Response:**
```json
{
  "total": 5,
  "history": [
    {
      "id": 42,
      "symptoms": "itching, skin_rash, nodal_skin_eruptions",
      "prediction": "Fungal infection",
      "confidence": 88.5,
      "severity": "Low",
      "doctor_recommendation": "Dermatologist",
      "created_at": "2026-10-22T17:50:00"
    }
  ]
}
```

### 3.2 Get Printable Medical Report
- **Endpoint:** `GET /history/{prediction_id}/report`
- **Headers:** `Authorization: Bearer <TOKEN>`
- **Response:** Structured JSON formatted for PDF export or clinical printout.

---

## 4. Appointments & Specialists Endpoints

### 4.1 List Verified Doctors
- **Endpoint:** `GET /doctors`
- **Response:** List of available specialists, clinics, experience, and ratings.

### 4.2 Book Appointment
- **Endpoint:** `POST /appointments`
- **Headers:** `Authorization: Bearer <TOKEN>`
- **Request Body:**
```json
{
  "doctor_id": 2,
  "doctor_name": "Dr. Marcus Vance, MD",
  "specialty": "Dermatologist",
  "appointment_date": "2026-10-25",
  "time_slot": "10:30 AM - 11:30 AM",
  "reason": "Rash follow-up"
}
```

### 4.3 List Patient Appointments
- **Endpoint:** `GET /appointments`
- **Headers:** `Authorization: Bearer <TOKEN>`

### 4.4 Cancel Appointment
- **Endpoint:** `DELETE /appointments/{appointment_id}`
- **Headers:** `Authorization: Bearer <TOKEN>`

---

## 5. Patient Profile & Wellness Tips

### 5.1 Get / Update Profile
- **Endpoint:** `GET /profile` and `PUT /profile`
- **Headers:** `Authorization: Bearer <TOKEN>`

### 5.2 Curated Health Tips
- **Endpoint:** `GET /health-tips`
