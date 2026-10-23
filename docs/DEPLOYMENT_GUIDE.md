# Cloud & Production Deployment Guide
## HealthAI - Disease Prediction System

This guide outlines options for deploying HealthAI to production web servers, clouds, and container registries.

---

## Option 1: 1-Click Deployment via Docker Compose (Recommended for VPS / Cloud VMs)

Ideal for **DigitalOcean Droplets**, **AWS EC2**, **Linode**, **Hetzner**, or any Ubuntu/Debian Linux server:

1. SSH into your server:
   ```bash
   ssh ubuntu@your-server-ip
   ```
2. Clone the repository:
   ```bash
   git clone https://github.com/Siddhartha07-H/AI_Disease_Prediction_System.git
   cd AI_Disease_Prediction_System
   ```
3. Set your production `.env` variables (generate a strong `JWT_SECRET_KEY`):
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
4. Start all services:
   ```bash
   docker compose up --build -d
   ```
5. Configure Nginx Reverse Proxy with SSL (Certbot Let's Encrypt) to point your domain (e.g. `https://healthai.yourdomain.com`) to `http://127.0.0.1:8000`.

---

## Option 2: Render / Railway Cloud Hosting

### Render.com Setup:
1. Create a **PostgreSQL Database** on Render. Note the connection string (`Internal Database URL`).
2. Create a **Web Service** on Render connected to this repository:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt && python database/init_db.py`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:**
     - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (from the Render Postgres service)
     - `JWT_SECRET_KEY`: (Secure random string)
     - `AI_MODEL_NAME`: `disease_model.pkl`

---

## Option 3: Android App Connection Configuration

When you host your backend at `https://healthai.yourdomain.com`:
1. In `android/app/src/main/res/values/strings.xml`, update:
   ```xml
   <string name="default_web_url">https://healthai.yourdomain.com</string>
   ```
2. Or in `android/app/src/main/java/com/healthai/diseaseprediction/MainActivity.kt`, update `targetUrl` to point to your live HTTPS domain.
3. Build the release `.aab` bundle and submit to Google Play Console!
