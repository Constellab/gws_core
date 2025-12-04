from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from gws_core.core.utils.settings import Settings
from gws_core.lab.system_dto import LabEnvironment


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to HTTP responses

    Note: X-Frame-Options is disabled to allow iframe embedding from any website.
    This reduces clickjacking protection but provides maximum iframe flexibility.
    CSP frame-ancestors directive is set to '*' for consistency.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response)

        return response

    def _add_security_headers(self, response: Response) -> None:
        """Add comprehensive security headers to the response"""

        # Content Security Policy
        csp_policy = self._get_csp_policy()
        response.headers["Content-Security-Policy"] = csp_policy

        # HTTP Strict Transport Security (HSTS)
        # Only add HSTS in production/cloud environments with HTTPS
        lab_env: LabEnvironment = Settings.get_lab_environment()
        if lab_env == "ON_CLOUD":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # X-Content-Type-Options - Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection - Enable XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy - Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy - Control browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "magnetometer=(), gyroscope=(), speaker=(), "
            "vibrate=(), fullscreen=(self), payment=()"
        )

    def _get_csp_policy(self) -> str:
        """Generate Content Security Policy based on environment"""
        lab_env: LabEnvironment = Settings.get_lab_environment()

        if lab_env == "ON_CLOUD":
            # Stricter CSP for production
            virtual_host = Settings.get_virtual_host()
            if virtual_host:
                return (
                    f"default-src 'self' https://*.{virtual_host}; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "font-src 'self' data:; "
                    "connect-src 'self' wss: https:; "
                    "frame-ancestors *; "
                    "base-uri 'self'; "
                    "form-action 'self'"
                )

        # More relaxed CSP for development
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss: http: https:; "
            "frame-ancestors *; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
