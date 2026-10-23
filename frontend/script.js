/**
 * HealthAI - Frontend Engine & Clinical Client
 * Fully compatible with Web Browsers, PWA, and Android WebView (Play Store)
 */

// =========================================================
// 1. DYNAMIC API RESOLUTION & NATIVE ANDROID BRIDGE
// =========================================================
const API_URL = (function () {
    const custom = localStorage.getItem("healthai_api_url");
    if (custom) return custom;

    if (window.location.origin && window.location.origin.startsWith("http")) {
        // If loaded from Live Server or custom port (e.g., 5500, 3000), target FastAPI backend on 8000
        if (window.location.port && window.location.port !== "8000") {
            return `${window.location.protocol}//${window.location.hostname}:8000`;
        }
        return window.location.origin;
    }
    return "http://127.0.0.1:8000";
})();

const isAndroidApp = () => typeof window.Android !== "undefined";

function triggerHaptic(duration = 50) {
    if (isAndroidApp() && window.Android.vibrate) {
        window.Android.vibrate(duration);
    } else if (navigator.vibrate) {
        navigator.vibrate(duration);
    }
}

function showNativeToast(message) {
    if (isAndroidApp() && window.Android.showToast) {
        window.Android.showToast(message);
    }
}

function shareMedicalReport(title, text) {
    if (isAndroidApp() && window.Android.shareReport) {
        window.Android.shareReport(title, text);
        return;
    }
    if (navigator.share) {
        navigator.share({ title, text }).catch(() => { });
        return;
    }
    // Fallback: copy to clipboard
    navigator.clipboard.writeText(`${title}\n\n${text}`).then(() => {
        alert("Report summary copied to clipboard!");
    });
}

// =========================================================
// 2. AUTHENTICATION & SESSION STATE
// =========================================================
function getAccessToken() {
    return sessionStorage.getItem("access_token") || localStorage.getItem("access_token");
}

function saveAuthSession(token, user, doctor = null) {
    sessionStorage.setItem("access_token", token);
    localStorage.setItem("access_token", token);
    if (user) {
        sessionStorage.setItem("user", JSON.stringify(user));
        sessionStorage.setItem("patient_name", user.full_name || "Patient");
        localStorage.setItem("user_role", user.role || "patient");
        localStorage.setItem("user_name", user.full_name || "Patient");
    }
    if (doctor) {
        localStorage.setItem("doctor_profile", JSON.stringify(doctor));
        sessionStorage.setItem("doctor_profile", JSON.stringify(doctor));
    }
}

function clearAuthSession() {
    sessionStorage.removeItem("access_token");
    localStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    sessionStorage.removeItem("patient_name");
    localStorage.removeItem("user_role");
    localStorage.removeItem("user_name");
    localStorage.removeItem("doctor_profile");
    sessionStorage.removeItem("doctor_profile");
}

function authHeaders(extra = {}) {
    const token = getAccessToken();
    return {
        ...extra,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
}

function getCurrentUser() {
    try {
        const raw = sessionStorage.getItem("user");
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

// =========================================================
// 3. GLOBAL APPLICATION STATE
// =========================================================
let allSymptomsDetailed = [];
const selectedSymptomsSet = new Set();
let activeCategory = "All";
let cachedDoctors = [];
let cachedHistory = [];

// =========================================================
// 4. INITIALIZATION ON DOM READY
// =========================================================
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initMobileNav();
    syncUserInfo();

    const isAuthPage = window.location.pathname.includes("login.html") ||
        window.location.pathname.includes("register.html");

    // Protect Dashboard and Symptom Checker pages
    if (!isAuthPage && !getAccessToken()) {
        window.location.replace("login.html");
        return;
    }

    // Attach form and button listeners
    initAuthForms();
    initLogoutHandlers();

    // Page-specific modules
    if (document.getElementById("symptoms-selector-container")) {
        loadSymptomsList();
    }

    if (document.getElementById("dashboard-history-list")) {
        loadDashboardStats();
        loadPredictionHistory();
        loadDoctorsList();
        loadAppointmentsList();
        loadHealthTips();
    }
});

// =========================================================
// 5. THEME & NAVIGATION
// =========================================================
function initTheme() {
    const savedTheme = localStorage.getItem("healthai_theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);

    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    if (themeToggleBtn) {
        themeToggleBtn.textContent = savedTheme === "dark" ? "☀️" : "🌙";
        themeToggleBtn.addEventListener("click", () => {
            const current = document.documentElement.getAttribute("data-theme");
            const next = current === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", next);
            localStorage.setItem("healthai_theme", next);
            themeToggleBtn.textContent = next === "dark" ? "☀️" : "🌙";
        });
    }
}

function initMobileNav() {
    const toggleBtn = document.getElementById("mobile-menu-toggle");
    const sidebar = document.querySelector(".sidebar");
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
        // Close on outside click
        document.addEventListener("click", (e) => {
            if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target) && sidebar.classList.contains("open")) {
                sidebar.classList.remove("open");
            }
        });
    }
}

function syncUserInfo() {
    const user = getCurrentUser();
    const name = user?.full_name || sessionStorage.getItem("patient_name") || "Patient";
    const initial = name.trim().charAt(0).toUpperCase() || "P";

    const nameElements = document.querySelectorAll(".user-name-display");
    nameElements.forEach((el) => { el.textContent = name; });

    const avatarElements = document.querySelectorAll(".user-avatar-display");
    avatarElements.forEach((el) => { el.textContent = initial; });

    const emailEl = document.getElementById("profile-display-email");
    if (emailEl && user?.email) {
        emailEl.textContent = user.email;
    }
}

function initLogoutHandlers() {
    const logoutBtns = document.querySelectorAll(".logout-trigger");
    logoutBtns.forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            clearAuthSession();
            showNativeToast("Logged out successfully");
            window.location.href = "login.html";
        });
    });
}

// =========================================================
// 6. AUTHENTICATION MODULE
// =========================================================
function initAuthForms() {
    // Login Form
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = loginForm.querySelector("button[type='submit']");
            const msgEl = document.getElementById("login-message");
            if (btn) btn.disabled = true;
            if (msgEl) msgEl.textContent = "Authenticating...";

            try {
                const res = await fetch(`${API_URL}/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        email: document.getElementById("email").value.trim(),
                        password: document.getElementById("password").value,
                    }),
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(typeof data.detail === "string" ? data.detail : "Login failed.");
                }

                saveAuthSession(data.access_token, data.user, data.doctor);
                triggerHaptic(50);
                showNativeToast(`Welcome back, ${data.user.full_name}!`);
                if (data.user && data.user.role === "doctor") {
                    if (msgEl) msgEl.textContent = "Doctor verified! Loading Clinical Command Center...";
                    setTimeout(() => { window.location.href = "doctor-dashboard.html"; }, 500);
                } else {
                    if (msgEl) msgEl.textContent = "Success! Redirecting to Dashboard...";
                    setTimeout(() => { window.location.href = "index.html"; }, 500);
                }
            } catch (err) {
                if (msgEl) msgEl.textContent = err.message || "Cannot connect to server.";
            } finally {
                if (btn) btn.disabled = false;
            }
        });
    }

    // Registration Form
    const registerForm = document.getElementById("register-form");
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = registerForm.querySelector("button[type='submit']");
            const msgEl = document.getElementById("register-message");
            if (btn) btn.disabled = true;
            if (msgEl) msgEl.textContent = "Creating patient account...";

            try {
                const res = await fetch(`${API_URL}/register`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        full_name: document.getElementById("full_name").value.trim(),
                        email: document.getElementById("email").value.trim(),
                        password: document.getElementById("password").value,
                    }),
                });
                const data = await res.json();
                if (res.status === 201) {
                    registerForm.reset();
                    triggerHaptic(60);
                    if (msgEl) msgEl.textContent = "Account registered successfully! Redirecting to login...";
                    setTimeout(() => { window.location.href = "login.html"; }, 1200);
                } else {
                    throw new Error(typeof data.detail === "string" ? data.detail : "Registration failed.");
                }
            } catch (err) {
                if (msgEl) msgEl.textContent = err.message || "Unable to register.";
            } finally {
                if (btn) btn.disabled = false;
            }
        });
    }
}

// =========================================================
// 7. SYMPTOM CHECKER & AI PREDICTION
// =========================================================
async function loadSymptomsList() {
    const container = document.getElementById("symptoms-selector-container");
    if (!container) return;

    container.innerHTML = "<div style='padding:20px;text-align:center;color:var(--text-muted);'>Loading clinical symptoms...</div>";

    try {
        const res = await fetch(`${API_URL}/symptoms`);
        const data = await res.json();

        allSymptomsDetailed = data.detailed || data.symptoms.map((s) => ({
            id: s,
            name: s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
            category: "General",
        }));

        renderCategoryPills();
        renderSymptomCheckboxes();
        initSymptomSearch();
        initPredictButton();
    } catch (err) {
        container.innerHTML = `<div style="padding:20px;color:var(--danger);">Error loading symptoms: ${err.message}. Check backend connection.</div>`;
    }
}

function renderCategoryPills() {
    const tray = document.getElementById("category-pills-bar");
    if (!tray) return;

    const categories = ["All", ...new Set(allSymptomsDetailed.map((s) => s.category))];
    tray.innerHTML = "";

    categories.forEach((cat) => {
        const pill = document.createElement("button");
        pill.type = "button";
        pill.className = `category-chip ${cat === activeCategory ? "active" : ""}`;
        pill.textContent = cat;
        pill.addEventListener("click", () => {
            activeCategory = cat;
            document.querySelectorAll(".category-chip").forEach((c) => c.classList.remove("active"));
            pill.classList.add("active");
            filterAndRenderSymptoms();
        });
        tray.appendChild(pill);
    });
}

function initSymptomSearch() {
    const searchInput = document.getElementById("symptom-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            filterAndRenderSymptoms();
        });
    }
}

function filterAndRenderSymptoms() {
    const query = (document.getElementById("symptom-search-input")?.value || "").toLowerCase().trim();

    const filtered = allSymptomsDetailed.filter((s) => {
        const matchesCategory = activeCategory === "All" || s.category === activeCategory;
        const matchesQuery = s.name.toLowerCase().includes(query) || s.id.toLowerCase().includes(query);
        return matchesCategory && matchesQuery;
    });

    renderSymptomCheckboxes(filtered);
}

function renderSymptomCheckboxes(items = allSymptomsDetailed) {
    const container = document.getElementById("symptoms-selector-container");
    if (!container) return;

    container.innerHTML = "";

    if (items.length === 0) {
        container.innerHTML = "<div style='padding:20px;text-align:center;color:var(--text-muted);'>No matching symptoms found.</div>";
        return;
    }

    items.forEach((item) => {
        const label = document.createElement("label");
        const isChecked = selectedSymptomsSet.has(item.id);
        label.className = `symptom-card-option ${isChecked ? "checked" : ""}`;

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = item.id;
        checkbox.checked = isChecked;

        checkbox.addEventListener("change", () => {
            if (checkbox.checked) {
                selectedSymptomsSet.add(item.id);
                label.classList.add("checked");
            } else {
                selectedSymptomsSet.delete(item.id);
                label.classList.remove("checked");
            }
            updateSelectedSymptomsTray();
        });

        const span = document.createElement("span");
        span.textContent = item.name;

        label.appendChild(checkbox);
        label.appendChild(span);
        container.appendChild(label);
    });
}

function updateSelectedSymptomsTray() {
    const tray = document.getElementById("selected-symptoms-tray");
    const countEl = document.getElementById("selected-symptoms-count");
    const predictBtn = document.getElementById("generate-prediction-btn");

    if (countEl) {
        const count = selectedSymptomsSet.size;
        countEl.textContent = `${count} symptom${count === 1 ? "" : "s"} selected ${count < 3 ? "(Minimum 3 required)" : "✓ Ready"}`;
        countEl.style.color = count >= 3 ? "var(--success)" : "var(--text-muted)";
    }

    if (predictBtn) {
        predictBtn.disabled = selectedSymptomsSet.size < 3;
    }

    if (!tray) return;
    tray.innerHTML = "";

    if (selectedSymptomsSet.size === 0) {
        tray.innerHTML = "<span style='color:var(--text-muted);font-size:13px;'>No symptoms selected yet. Click any symptoms above to add.</span>";
        return;
    }

    selectedSymptomsSet.forEach((symId) => {
        const sym = allSymptomsDetailed.find((s) => s.id === symId);
        const name = sym ? sym.name : symId.replace(/_/g, " ");

        const tag = document.createElement("span");
        tag.className = "selected-tag";
        tag.innerHTML = `${name} <button type="button" aria-label="Remove symptom">&times;</button>`;

        tag.querySelector("button").addEventListener("click", () => {
            selectedSymptomsSet.delete(symId);
            updateSelectedSymptomsTray();
            // Uncheck in grid
            const box = document.querySelector(`input[value="${symId}"]`);
            if (box) {
                box.checked = false;
                box.closest(".symptom-card-option")?.classList.remove("checked");
            }
        });

        tray.appendChild(tag);
    });
}

function initPredictButton() {
    const btn = document.getElementById("generate-prediction-btn");
    if (!btn) return;

    btn.addEventListener("click", async () => {
        if (selectedSymptomsSet.size < 3) {
            alert("Please select at least 3 symptoms before generating a prediction.");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = "Processing AI Clinical Analysis...";

        const resultCard = document.getElementById("prediction-results-card");
        if (resultCard) resultCard.style.display = "none";

        try {
            const res = await fetch(`${API_URL}/predict`, {
                method: "POST",
                headers: authHeaders({ "Content-Type": "application/json" }),
                body: JSON.stringify({ symptoms: Array.from(selectedSymptomsSet) }),
            });

            if (res.status === 401) {
                clearAuthSession();
                alert("Session expired. Please log in again.");
                window.location.href = "login.html";
                return;
            }

            const data = await res.json();
            if (!res.ok) {
                throw new Error(typeof data.detail === "string" ? data.detail : "Prediction failed.");
            }

            triggerHaptic(120);
            renderPredictionResults(data);
        } catch (err) {
            alert(`AI Analysis Error: ${err.message}`);
        } finally {
            btn.disabled = false;
            btn.innerHTML = "Generate AI Prediction →";
        }
    });
}

function renderPredictionResults(data) {
    const card = document.getElementById("prediction-results-card");
    if (!card) return;

    // Primary Diagnosis & Badges
    const nameEl = document.getElementById("result-disease-name");
    const confEl = document.getElementById("result-confidence-pill");
    const sevEl = document.getElementById("result-severity-pill");
    const specialistEl = document.getElementById("result-specialist-name");
    const emergencyAlert = document.getElementById("result-emergency-alert");

    if (nameEl) nameEl.textContent = data.display_name || data.prediction;
    if (confEl) confEl.textContent = `${data.confidence || 85}% AI Confidence`;

    if (sevEl) {
        sevEl.textContent = `${data.severity} Severity`;
        sevEl.className = `severity-pill ${(data.severity || "moderate").toLowerCase()}`;
    }

    if (specialistEl) {
        specialistEl.textContent = data.specialist || "General Physician";
    }

    if (emergencyAlert) {
        if (data.is_emergency) {
            emergencyAlert.style.display = "flex";
            const symList = data.emergency_symptoms_detected?.join(", ");
            emergencyAlert.querySelector(".emergency-text").textContent =
                `CRITICAL: High-risk indicators detected (${symList || "Acute Condition"}). Seek emergency healthcare immediately!`;
        } else {
            emergencyAlert.style.display = "none";
        }
    }

    // Differentials Chart
    const diffContainer = document.getElementById("differentials-container");
    if (diffContainer && data.differential_diagnoses) {
        diffContainer.innerHTML = "";
        data.differential_diagnoses.forEach((d) => {
            const row = document.createElement("div");
            row.className = "differentials-bar-row";
            row.innerHTML = `
                <div class="differentials-labels">
                    <span>${d.display_name || d.disease}</span>
                    <span>${d.probability}%</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${d.probability}%;"></div>
                </div>
            `;
            diffContainer.appendChild(row);
        });
    }

    // Precautions
    const precList = document.getElementById("result-precautions-list");
    if (precList && data.precautions) {
        precList.innerHTML = "";
        data.precautions.forEach((p) => {
            const li = document.createElement("li");
            li.textContent = p;
            precList.appendChild(li);
        });
    }

    // Medications & Diet
    const medList = document.getElementById("result-medications-list");
    if (medList && data.medications) {
        medList.innerHTML = "";
        data.medications.forEach((m) => {
            const li = document.createElement("li");
            li.textContent = m;
            medList.appendChild(li);
        });
    }

    // Book Specialist Button
    const bookSpecialistBtn = document.getElementById("book-specialist-btn");
    if (bookSpecialistBtn) {
        bookSpecialistBtn.onclick = () => {
            openAppointmentModalWithSpecialty(data.specialist);
        };
    }

    // Share & Print Buttons
    const shareBtn = document.getElementById("share-report-btn");
    if (shareBtn) {
        shareBtn.onclick = () => {
            shareMedicalReport(
                `HealthAI Report: ${data.display_name}`,
                `AI-Predicted Condition: ${data.display_name}\nConfidence: ${data.confidence}%\nRecommended Specialist: ${data.specialist}\nStatus: Doctor Review Required\n\nPrecautions:\n- ${data.precautions.join("\n- ")}`
            );
        };
    }

    const printBtn = document.getElementById("print-report-btn");
    if (printBtn) {
        printBtn.onclick = () => {
            window.print();
        };
    }

    card.style.display = "block";
    card.scrollIntoView({ behavior: "smooth" });
}

// =========================================================
// 8. DASHBOARD MODULES
// =========================================================
async function loadDashboardStats() {
    try {
        const histRes = await fetch(`${API_URL}/history`, { headers: authHeaders() });
        const histData = await histRes.json();
        const count = histData.total || 0;

        const countEl = document.getElementById("stat-total-predictions");
        if (countEl) countEl.textContent = count;

        const aptRes = await fetch(`${API_URL}/appointments`, { headers: authHeaders() });
        const aptData = await aptRes.json();
        const aptCount = aptData.total || 0;

        const aptEl = document.getElementById("stat-total-appointments");
        if (aptEl) aptEl.textContent = aptCount;
    } catch (err) {
        console.warn("Stats load error:", err);
    }
}

async function loadPredictionHistory() {
    const list = document.getElementById("dashboard-history-list");
    if (!list) return;

    list.innerHTML = "<div style='padding:16px;text-align:center;color:var(--text-muted);'>Loading records...</div>";

    try {
        const res = await fetch(`${API_URL}/history`, { headers: authHeaders() });
        const data = await res.json();
        cachedHistory = data.history || [];

        if (cachedHistory.length === 0) {
            list.innerHTML = "<div style='padding:20px;text-align:center;color:var(--text-muted);'>No past predictions yet. Run your first symptom check!</div>";
            return;
        }

        list.innerHTML = "";
        cachedHistory.forEach((item) => {
            const article = document.createElement("article");
            article.className = "history-item";

            const dateStr = item.created_at ? new Date(item.created_at).toLocaleDateString(undefined, {
                year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
            }) : "Recent";

            article.innerHTML = `
                <div class="history-item-details">
                    <h4>${item.prediction}</h4>
                    <p>Symptoms: ${item.symptoms} • ${dateStr}</p>
                </div>
                <div class="history-actions">
                    <span class="severity-pill ${(item.severity || "moderate").toLowerCase()}">${item.severity || "Moderate"}</span>
                    <button class="btn btn-outline" style="padding:6px 14px;font-size:12px;" onclick="viewReportModal(${item.id})">View Report</button>
                </div>
            `;
            list.appendChild(article);
        });
    } catch (err) {
        list.innerHTML = `<div style="padding:16px;color:var(--danger);">Unable to load history: ${err.message}</div>`;
    }
}

async function viewReportModal(predictionId) {
    const modal = document.getElementById("report-modal");
    const body = document.getElementById("report-modal-body");
    if (!modal || !body) return;

    body.innerHTML = "<div style='padding:30px;text-align:center;'>Fetching clinical report...</div>";
    modal.style.display = "flex";

    try {
        const res = await fetch(`${API_URL}/history/${predictionId}/report`, { headers: authHeaders() });
        const data = await res.json();

        body.innerHTML = `
            <div style="border-bottom:2px solid var(--border);padding-bottom:16px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <h2 style="color:var(--primary);">${data.diagnosis_data.display_name}</h2>
                    <span class="confidence-pill">${data.diagnosis_data.confidence}% Confidence</span>
                </div>
                <p style="font-size:12px;color:var(--text-muted);">Report ID: ${data.report_id} • Date: ${new Date(data.generated_at).toLocaleString()}</p>
            </div>

            <div style="background:var(--bg-page);padding:14px;border-radius:var(--radius-sm);margin-bottom:16px;font-size:13px;">
                <strong>Patient:</strong> ${data.patient.name} (${data.patient.email || "Confidential"})<br>
                <strong>Recommended Specialist:</strong> ${data.diagnosis_data.specialist}<br>
                <strong>Reported Symptoms:</strong> ${data.diagnosis_data.symptoms_reported.join(", ")}
            </div>

            <h4 style="margin-bottom:8px;">Recommended Clinical Precautions</h4>
            <ul style="font-size:13px;color:var(--text-secondary);margin-bottom:16px;padding-left:20px;">
                ${data.diagnosis_data.precautions.map((p) => `<li>${p}</li>`).join("")}
            </ul>

            <div style="background:#fffbeb;border:1px solid #fef3c7;padding:12px;border-radius:var(--radius-sm);font-size:12px;color:#92400e;">
                ⚠️ <strong>Clinical Disclaimer:</strong> ${data.disclaimer}
            </div>

            <div style="display:flex;gap:10px;margin-top:20px;justify-content:flex-end;">
                <button class="btn btn-outline" onclick="window.print()">Print Report</button>
                <button class="btn btn-accent" onclick="document.getElementById('report-modal').style.display='none'">Close</button>
            </div>
        `;
    } catch (err) {
        body.innerHTML = `<div style="color:var(--danger);">Error loading report: ${err.message}</div>`;
    }
}

// =========================================================
// 9. DOCTOR APPOINTMENTS MODULE
// =========================================================
async function loadDoctorsList() {
    try {
        const res = await fetch(`${API_URL}/doctors`);
        const data = await res.json();
        cachedDoctors = data.doctors || [];

        const select = document.getElementById("appointment-doctor-select");
        if (select) {
            select.innerHTML = '<option value="">-- Select a Specialist --</option>';
            cachedDoctors.forEach((doc) => {
                const opt = document.createElement("option");
                opt.value = doc.id;
                opt.dataset.specialty = doc.specialty;
                opt.dataset.name = doc.name;
                opt.textContent = `${doc.name} (${doc.specialty}) - ⭐ ${doc.rating}`;
                select.appendChild(opt);
            });
        }
    } catch (err) {
        console.warn("Doctors load error:", err);
    }
}

async function loadAppointmentsList() {
    const list = document.getElementById("dashboard-appointments-list");
    if (!list) return;

    try {
        const res = await fetch(`${API_URL}/appointments`, { headers: authHeaders() });
        const data = await res.json();
        const appointments = data.appointments || [];

        if (appointments.length === 0) {
            list.innerHTML = "<div style='padding:16px;color:var(--text-muted);font-size:13px;'>No upcoming appointments scheduled.</div>";
            return;
        }

        list.innerHTML = "";
        appointments.forEach((apt) => {
            const div = document.createElement("div");
            div.className = "history-item";
            div.innerHTML = `
                <div>
                    <h4>${apt.doctor_name}</h4>
                    <p>${apt.specialty} • ${apt.appointment_date} at ${apt.time_slot}</p>
                </div>
                <div class="history-actions">
                    <span class="severity-pill low">${apt.status}</span>
                    ${apt.status !== "Cancelled" ? `<button class="btn btn-outline" style="padding:4px 10px;font-size:11px;color:var(--danger);" onclick="cancelAppointmentHandler(${apt.id})">Cancel</button>` : ""}
                </div>
            `;
            list.appendChild(div);
        });
    } catch (err) {
        list.innerHTML = `<div style="color:var(--danger);font-size:13px;">Error: ${err.message}</div>`;
    }
}

function openAppointmentModalWithSpecialty(specialty) {
    const modal = document.getElementById("book-appointment-modal");
    if (!modal) return;

    modal.style.display = "flex";
    const select = document.getElementById("appointment-doctor-select");
    if (select && specialty) {
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].dataset.specialty &&
                select.options[i].dataset.specialty.toLowerCase().includes(specialty.toLowerCase())) {
                select.selectedIndex = i;
                break;
            }
        }
    }
}

async function cancelAppointmentHandler(appointmentId) {
    if (!confirm("Are you sure you want to cancel this appointment?")) return;
    try {
        const res = await fetch(`${API_URL}/appointments/${appointmentId}`, {
            method: "DELETE",
            headers: authHeaders(),
        });
        if (res.ok) {
            triggerHaptic(50);
            showNativeToast("Appointment cancelled");
            loadAppointmentsList();
            loadDashboardStats();
        } else {
            alert("Could not cancel appointment.");
        }
    } catch (err) {
        alert(err.message);
    }
}

const appointmentForm = document.getElementById("book-appointment-form");
if (appointmentForm) {
    appointmentForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const select = document.getElementById("appointment-doctor-select");
        const selectedOpt = select.options[select.selectedIndex];
        const docId = selectedOpt.value ? parseInt(selectedOpt.value, 10) : null;
        const docName = selectedOpt.dataset.name || "Specialist Doctor";
        const specialty = selectedOpt.dataset.specialty || "General Medicine";

        const payload = {
            doctor_id: docId,
            doctor_name: docName,
            specialty: specialty,
            appointment_date: document.getElementById("apt-date").value,
            time_slot: document.getElementById("apt-time").value,
            reason: document.getElementById("apt-reason").value,
        };

        try {
            const res = await fetch(`${API_URL}/appointments`, {
                method: "POST",
                headers: authHeaders({ "Content-Type": "application/json" }),
                body: JSON.stringify(payload),
            });
            if (res.ok) {
                triggerHaptic(80);
                showNativeToast("Appointment confirmed!");
                document.getElementById("book-appointment-modal").style.display = "none";
                appointmentForm.reset();
                loadAppointmentsList();
                loadDashboardStats();
            } else {
                const err = await res.json();
                alert(err.detail || "Booking failed.");
            }
        } catch (err) {
            alert(err.message);
        }
    });
}

// =========================================================
// 10. HEALTH TIPS & WELLNESS
// =========================================================
async function loadHealthTips() {
    const container = document.getElementById("health-tips-container");
    if (!container) return;

    try {
        const res = await fetch(`${API_URL}/health-tips`);
        const data = await res.json();
        const tips = data.tips || [];

        container.innerHTML = "";
        tips.forEach((tip) => {
            const card = document.createElement("div");
            card.className = "feature-box";
            card.innerHTML = `
                <div class="feature-icon-badge">🌿</div>
                <h3>${tip.title}</h3>
                <p>${tip.content}</p>
                <span class="category-chip" style="align-self:flex-start;">${tip.category}</span>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.warn("Tips load error:", err);
    }
}

// Close any open modal on outside click
window.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) {
        e.target.style.display = "none";
    }
});
