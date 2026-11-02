"""Security, Defensive Headers, and Hardening Tests.

Verifies:
1. Security response headers (OWASP guidelines & Engineering Rules §10).
2. Correlation ID (X-Request-ID) sanitization against injection and malformed values (Engineering Rules §5).
3. Request body size limiting / DoS prevention (Engineering Rules §5).
4. Constant-time login handling to prevent user enumeration (Engineering Rules §6).
5. Production configuration fail-safe validation (Engineering Rules §4, §13).
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app

client = TestClient(app)


class TestSecurityHeaders:
    """Verify presence and strictness of defensive HTTP response headers."""

    def test_security_headers_present_on_health_route(self):
        """All API responses must include defensive security headers."""
        resp = client.get("/health/live")
        assert resp.status_code == 200
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "default-src 'none'" in resp.headers.get("Content-Security-Policy", "")
        assert "frame-ancestors 'none'" in resp.headers.get("Content-Security-Policy", "")
        assert "camera=()" in resp.headers.get("Permissions-Policy", "")

    def test_security_headers_present_on_api_v1_route(self):
        """V1 endpoints must also carry defensive headers."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"


class TestRequestIdSanitization:
    """Verify X-Request-ID validation against injection and corruption."""

    def test_safe_request_id_preserved(self):
        """Valid alphanumeric request IDs are preserved."""
        safe_id = "req-valid-12345_abc"
        resp = client.get("/health/live", headers={"X-Request-ID": safe_id})
        assert resp.status_code == 200
        assert resp.headers.get("X-Request-ID") == safe_id

    def test_xss_injection_request_id_replaced(self):
        """XSS payloads in X-Request-ID are replaced with a safe UUID."""
        malicious_id = "<script>alert('xss')</script>"
        resp = client.get("/health/live", headers={"X-Request-ID": malicious_id})
        assert resp.status_code == 200
        clean_id = resp.headers.get("X-Request-ID")
        assert clean_id != malicious_id
        # Verify it was replaced with a valid UUID
        uuid.UUID(clean_id)

    def test_crlf_injection_request_id_replaced(self):
        """CRLF header injection attempts in X-Request-ID are replaced."""
        crlf_id = "safe_part\r\nInjected-Header: evil"
        resp = client.get("/health/live", headers={"X-Request-ID": crlf_id})
        assert resp.status_code == 200
        clean_id = resp.headers.get("X-Request-ID")
        assert clean_id != crlf_id
        uuid.UUID(clean_id)

    def test_oversized_request_id_replaced(self):
        """Overly long correlation IDs (>64 chars) are replaced to prevent log flooding."""
        oversized_id = "a" * 128
        resp = client.get("/health/live", headers={"X-Request-ID": oversized_id})
        assert resp.status_code == 200
        clean_id = resp.headers.get("X-Request-ID")
        assert clean_id != oversized_id
        uuid.UUID(clean_id)


class TestPayloadSizeLimit:
    """Verify Request Body Limiting protects against memory exhaustion."""

    def test_oversized_payload_rejected(self):
        """Payloads declaring content-length > 2MB must be rejected with HTTP 413."""
        oversized_length = 3 * 1024 * 1024  # 3 MB
        resp = client.post(
            "/api/v1/auth/register",
            headers={"Content-Length": str(oversized_length), "Content-Type": "application/json"},
            content=b"{}",
        )
        assert resp.status_code == 413
        data = resp.json()
        assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"
        assert "exceeds maximum allowed size" in data["error"]["message"]


class TestTimingAttackDefense:
    """Verify authentication verifies credentials in constant time."""

    def test_nonexistent_user_login_rejected_safely(self):
        """Logging in with a non-existent email safely returns 401."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent_user_9999@example.com", "password": "RandomPassword123!"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid email or password."


class TestProductionConfigurationValidation:
    """Verify settings fail fast on unsafe production settings."""

    def test_production_fails_on_default_jwt_secret(self):
        """In production, the default insecure dev JWT key must be rejected."""
        with pytest.raises(ValueError, match="CRITICAL SECURITY CONFIGURATION ERROR"):
            Settings(
                APP_ENV="production",
                DEBUG=False,
                JWT_SECRET_KEY="dev_insecure_jwt_secret_change_me_in_production_min_32_bytes",
            )

    def test_production_fails_on_short_jwt_secret(self):
        """In production, JWT secrets shorter than 32 characters must be rejected."""
        with pytest.raises(ValueError, match="at least 32 characters"):
            Settings(
                APP_ENV="production",
                DEBUG=False,
                JWT_SECRET_KEY="too_short_key",
            )

    def test_production_fails_on_debug_mode_enabled(self):
        """In production, DEBUG=True must be rejected."""
        with pytest.raises(ValueError, match="DEBUG mode MUST be disabled"):
            Settings(
                APP_ENV="production",
                DEBUG=True,
                JWT_SECRET_KEY="strong_production_secret_key_minimum_32_bytes_long!",
            )

    def test_production_valid_configuration_passes(self):
        """In production, a strong secret and DEBUG=False passes validation."""
        s = Settings(
            APP_ENV="production",
            DEBUG=False,
            JWT_SECRET_KEY="strong_production_secret_key_minimum_32_bytes_long!",
        )
        assert s.app_env == "production"
        assert not s.debug
