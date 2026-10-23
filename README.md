# 🩺 HealthAI — AI Disease Prediction & Healthcare Management System

[![Python Version](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.142-009688.svg)](https://fastapi.tiangolo.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-v1.9-F7931E.svg)](https://scikit-learn.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/Tests-26%20Passing-brightgreen.svg)](tests/)

An enterprise-ready, cross-platform artificial intelligence clinical decision-support and patient management system. The system evaluates 132 distinct symptoms across 41 human medical conditions, generates probabilistic differential diagnoses, provides clinical precautions and safe medication guidelines, books specialist doctor appointments, includes a dedicated Doctor Clinical Management Portal, and outputs printable clinical reports.

Fully prepared and optimized for **Web Hosting**, **PWA Mobile Access**, and **Docker Containers**.

---

## 🏗️ System Architecture

```
AI_Disease_Prediction_System/
├── backend/                   # FastAPI high-performance asynchronous API
│   ├── main.py                # REST endpoints, prediction engine, static hosting
│   ├── database.py            # PostgreSQL connection pool and CRUD operations
│   ├── auth.py                # Patient & Doctor registration, login, and JWT tokens
│   ├── security.py            # Bearer token verification and RBAC
│   └── security_middleware.py # Rate-limiting, OWASP security headers, DDoS defense
├── frontend/                  # Modern, responsive clinical portal & PWA
│   ├── index.html             # Patient dashboard, reports, appointments, stats
│   ├── predict.html           # Multi-symptom selector and diagnostic result view
│   ├── login.html             # Patient sign-in with demo helper
│   ├── register.html          # Patient onboarding
│   ├── doctor-login.html      # Doctor & specialist sign-in
│   ├── doctor-register.html   # Medical practitioner licensing onboarding
│   ├── doctor-dashboard.html  # Doctor consultation queue and patient records
│   ├── privacy.html           # Health & medical privacy policy
│   ├── terms.html             # Clinical liability agreement & terms of use
│   ├── style.css              # Custom medical design system (Plus Jakarta Sans)
│   ├── script.js              # Client engine, dynamic API resolution
│   ├── manifest.json          # Progressive Web App (PWA) manifest
│   └── sw.js                  # Service Worker for offline caching
├── database/                  # Relational database scripts
│   ├── schema.sql             # Table schemas, foreign keys, and indexes
│   ├── init_db.py             # One-step database migration and seeder
│   └── disease_info.json      # Clinical factsheet for 41 diseases
├── ai_model/                  # Trained Machine Learning artifacts
│   ├── disease_model.pkl      # Decision Tree classifier (132 features)
│   ├── random_forest_candidate.pkl # Random Forest probability model
│   └── train_model.py         # Training and evaluation script
├── tests/                     # Automated Pytest test suite (26 tests)
│   ├── test_ai_model.py       # Model accuracy and probability tests
│   ├── test_auth.py           # Password hashing and JWT security tests
│   ├── test_predict_api.py    # Endpoint validations and safety safeguards
│   ├── test_database.py       # Database persistence and relations tests
│   ├── test_doctor.py         # Doctor registration, login, and dashboard tests
│   └── test_security_and_load.py # Security headers, rate limiting & concurrency tests
├── docs/                      # Production guides
│   ├── API_DOCUMENTATION.md   # Complete REST API reference
│   └── DEPLOYMENT_GUIDE.md    # Cloud and Docker deployment instructions
├── Dockerfile                 # Production container image
├── docker-compose.yml         # 1-command container orchestration (Postgres + App)
└── requirements.txt           # Python dependencies
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- PostgreSQL (or use Docker)

### 2. Setup Environment
```bash
# Clone the repository
cd AI_Disease_Prediction_System

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize the Database
Configure your database credentials in `.env` (or use the defaults), then run:
```bash
python database/init_db.py
```
*This automatically creates all necessary tables (`users`, `user_profiles`, `prediction_history`, `doctors`, `appointments`, `health_tips`) and seeds verified specialists.*

### 4. Run the Full Application (Web + API)
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Open **`http://127.0.0.1:8000`** in your browser to access the complete Patient Dashboard!

---

## 🧪 Automated Testing

The project includes a 20-test automated test suite covering models, authentication, API routes, and database operations.

To run all tests:
```bash
pytest -v
```
Output:
```
tests/test_ai_model.py ......                     [ 25%]
tests/test_auth.py ..                             [ 35%]
tests/test_database.py ....                       [ 55%]
tests/test_predict_api.py .........               [100%]
======================== 20 passed in 4.28s ========================
```

---

## 🐳 Docker Deployment

Deploy the complete stack (PostgreSQL database + FastAPI backend + Web portal) with a single command:
```bash
docker-compose up --build -d
```
Access the application at `http://localhost:8000`.

---

## 🛡️ Medical Disclaimer
HealthAI is an informational decision-support tool powered by machine learning algorithms. It is **not** a certified clinical diagnosis or medical prescription tool. In case of emergency or severe symptoms, users must seek immediate emergency medical care.