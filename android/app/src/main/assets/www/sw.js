/**
 * HealthAI - Service Worker for Offline Caching and Fast Loads
 */

const CACHE_NAME = "healthai-v2.1";
const STATIC_ASSETS = [
    "/",
    "/index.html",
    "/predict.html",
    "/login.html",
    "/register.html",
    "/doctor-login.html",
    "/doctor-register.html",
    "/doctor-dashboard.html",
    "/privacy.html",
    "/terms.html",
    "/style.css",
    "/script.js"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener("fetch", (event) => {
    // Only intercept GET requests for static assets
    if (event.request.method !== "GET" || event.request.url.includes("/api/") || event.request.url.includes("/predict")) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((networkResponse) => {
                // Cache fresh copies of static assets
                if (networkResponse && networkResponse.status === 200) {
                    const cloned = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, cloned));
                }
                return networkResponse;
            })
            .catch(() => caches.match(event.request))
    );
});
