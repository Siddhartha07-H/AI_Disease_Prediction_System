# Google Play Store Deployment & Release Guide
## HealthAI - Disease Prediction System

This document provides complete instructions to build, sign, and publish the **HealthAI** Android application to the **Google Play Store**, fully compliant with Google Play's Medical & Health Apps Developer Policies.

---

## 1. Project Specifications
- **Package Name:** `com.healthai.diseaseprediction`
- **Application Name:** HealthAI
- **Min SDK:** 24 (Android 7.0 Nougat+)
- **Target SDK:** 34 (Android 14, required for Play Console 2024/2026 submissions)
- **Version Code:** 1
- **Version Name:** 1.0.0
- **App Category:** Medical / Health & Fitness

---

## 2. Generating a Signed Release App Bundle (.AAB)

Google Play Store requires an **Android App Bundle (.aab)** for all new application submissions.

### Step 2.1: Generate Your Private Keystore
In PowerShell or terminal:
```bash
keytool -genkey -v -keystore healthai-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias healthai_release_alias
```
*Keep your `.jks` file and passwords safe and backed up.*

### Step 2.2: Configure `keystore.properties`
Inside `android/`:
```properties
storeFile=../healthai-release-key.jks
storePassword=YourKeystorePassword
keyAlias=healthai_release_alias
keyPassword=YourKeyPassword
```

### Step 2.3: Build the Release Bundle via Android Studio or Terminal
From the `android/` directory:
```bash
# Windows
.\gradlew.bat bundleRelease

# Linux / macOS
./gradlew bundleRelease
```
The compiled App Bundle will be located at:
```
android/app/build/outputs/bundle/release/app-release.aab
```

---

## 3. Google Play Console Setup & Questionnaire Checklist

### 3.1: App Details
- **App Name:** `HealthAI - Disease Prediction & Health Assistant` (Max 30 chars: `HealthAI - Disease Predictor`)
- **Short Description:** `AI-powered symptom checker, differential diagnoses, and doctor appointments.` (Max 80 chars)
- **Full Description:**
  > Take control of your personal health with HealthAI. Enter your observed symptoms to receive instant machine-learning clinical decision-support predictions, differential diagnoses, and actionable health precautions.
  >
  > ✨ Key Features:
  > • AI Symptom Checker covering 132 symptoms and 41 medical conditions.
  > • Differential diagnoses with probabilistic confidence scores.
  > • Curated clinical precautions, dietary advice, and safe guidelines.
  > • Verified Doctor Directory & Appointment Booking across medical specialties.
  > • Printable and shareable Medical Summaries for your physician.
  > • Strict privacy: All health data is encrypted and confidential.
  >
  > ⚠️ Medical Disclaimer: HealthAI provides informational decision support and does not provide confirmed clinical diagnoses. Always consult a licensed healthcare professional for medical advice.

### 3.2: Store Assets
- **App Icon:** 512x512 PNG, 32-bit color (generated in `frontend/icon-512.png`).
- **Feature Graphic:** 1024x500 PNG/JPEG (landscape header).
- **Screenshots:** Minimum 2 phone screenshots (1080x1920 or 1080x2400 recommended).

---

## 4. Google Play Medical App Policy Compliance (MANDATORY)

Google Play has strict policies for Medical & Health apps. Fill out the **App Content -> Health Apps** declaration as follows:

1. **Category Selection:** Select **"Medical Information and Education"** or **"Clinical Decision Support"**.
2. **Medical Disclaimer:** The application must display an explicit disclaimer (already built into the app header and footer):
   > *"HealthAI is an informational decision-support tool. It does not diagnose, treat, or prevent any disease. Consult a licensed doctor for medical decisions."*
3. **Emergency Care:** The app must advise users to seek emergency care for severe symptoms (already implemented in `emergency-banner` and SOS triggers).
4. **Privacy Policy URL:** Enter your public privacy policy URL:
   `https://yourdomain.com/privacy` or host `frontend/privacy.html`.
5. **Data Safety Form:**
   - Health info: Yes, collected (symptoms and optional profile), encrypted in transit, optional, user can delete.
   - Financial info: No.
   - Location: No.
   - User account info: Yes (name, email) for authentication.

---

## 5. Release Tracks Workflow

1. Go to **Google Play Console -> Release -> Testing -> Internal Testing**.
2. Create a new release and upload `app-release.aab`.
3. Add internal test email addresses and install via the test link.
4. Verify all features (symptom checker, appointment booking, report sharing).
5. Promote release to **Closed Testing** or **Production** for Google review!
