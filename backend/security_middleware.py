"""
HealthAI Security & Traffic Management Middleware
- In-memory sliding-window rate limiting (DoS / brute-force protection)
- HTTP security headers (OWASP standards)
- Static asset caching & payload flood protection
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityAndTrafficMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_payload_bytes: int = 2 * 1024 * 1024):
        super().__init__(app)
        self.max_payload_bytes = max_payload_bytes
        self._lock = Lock()
        # Storage format: { ip: [(timestamp, route_type)] }
        self._rate_records: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        self._last_cleanup = time.time()

        # Rate limits per minute
        self.LIMITS = {
            "auth": 25,       # /login, /register, /doctor/*
            "predict": 60,    # /predict
            "api": 300,       # standard API endpoints
        }

    def _classify_route(self, path: str) -> str:
        p = path.lower()
        if any(p.startswith(x) for x in ["/login", "/register", "/doctor/login", "/doctor/register"]):
            return "auth"
        if p.startswith("/predict"):
            return "predict"
        return "api"

    def _cleanup_stale_records(self, now: float):
        """Purge IP records older than 2 minutes to keep memory footprint bounded."""
        if now - self._last_cleanup > 120.0:
            threshold = now - 60.0
            stale_ips = []
            for ip, records in self._rate_records.items():
                active = [r for r in records if r[0] > threshold]
                if active:
                    self._rate_records[ip] = active
                else:
                    stale_ips.append(ip)
            for ip in stale_ips:
                del self._rate_records[ip]
            self._last_cleanup = now

    def _is_rate_limited(self, ip: str, route_type: str, now: float) -> Tuple[bool, int]:
        window_start = now - 60.0
        limit = self.LIMITS.get(route_type, self.LIMITS["api"])

        with self._lock:
            self._cleanup_stale_records(now)
            records = self._rate_records[ip]
            # Filter to active window and route
            matching = [r for r in records if r[0] > window_start and r[1] == route_type]

            if len(matching) >= limit:
                # Calculate retry after
                oldest_in_window = min(r[0] for r in matching)
                retry_after = max(1, int(60.0 - (now - oldest_in_window)))
                return True, retry_after

            # Record this request
            records.append((now, route_type))
            return False, 0

    async def dispatch(self, request: Request, call_next) -> Response:
        now = time.time()

        # 1. Payload size check
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_payload_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Payload Too Large",
                            "detail": f"Request body exceeds maximum allowed size of {self.max_payload_bytes // (1024*1024)} MB."
                        }
                    )
            except ValueError:
                pass

        # 2. Rate limiting check (applied to API & Auth endpoints, skipped for static files)
        path = request.url.path
        is_static = any(
            path.startswith(prefix) for prefix in ["/static", "/favicon.ico"]
        ) or any(path.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".svg", ".json", ".ico"])

        if not is_static:
            client_ip = request.client.host if request.client else "127.0.0.1"
            # Forwarded-For header support for reverse proxies / Cloudflare / Pinggy
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()

            route_type = self._classify_route(path)
            is_limited, retry_after = self._is_rate_limited(client_ip, route_type, now)

            if is_limited:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": f"Too many requests to '{path}'. Please slow down and try again.",
                        "retry_after_seconds": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)}
                )

        # 3. Process request
        response: Response = await call_next(request)

        # 4. Attach standard HTTP security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # 5. Traffic load optimization: Cache headers for static assets, no-cache for private health data
        if is_static:
            # Tell browsers to cache static files for 1 hour to reduce heavy network traffic
            response.headers["Cache-Control"] = "public, max-age=3600, must-revalidate"
        elif path.startswith("/api/") or path.startswith("/predict") or path.startswith("/doctor"):
            # Never cache private medical or auth data
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

        return response
