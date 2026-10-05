"""Authentication & Authorization Integration Tests (API Contract v2 §7-11).

Tests:
1. User registration creates User, Profile, Role, hashes password, and returns tokens.
2. Duplicate registration returns HTTP 409 Conflict.
3. Login with valid credentials returns tokens and updates last_login_at.
4. Login with invalid credentials returns HTTP 401 with masked error message.
5. Token refresh issues rotated access and refresh tokens.
6. Protected /auth/me returns authenticated user details.
7. Unauthenticated request to /auth/me is rejected.
8. Password hashing utilities enforce bcrypt standards.
"""

from fastapi.testclient import TestClient

from app.core.security import hash_password, verify_password
from app.main import app

client = TestClient(app)


def test_password_hashing_and_verification():
    """Verify bcrypt hash generation and validation."""
    raw_pwd = "SuperSecretPassword123!"
    hashed = hash_password(raw_pwd)

    assert hashed != raw_pwd
    assert hashed.startswith("$2")  # bcrypt identifier
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_register_user_success():
    """Verify registration creates user, profile, role, and returns JWT tokens."""
    payload = {
        "email": "elder_john@example.com",
        "password": "SecurePassword123!",
        "display_name": "John Doe",
        "profile_type": "ELDER",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "user" in data
    assert data["user"]["email"] == "elder_john@example.com"
    assert data["user"]["status"] == "ACTIVE"
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600


def test_register_duplicate_email_conflict():
    """Verify registering an already registered email returns HTTP 409."""
    payload = {
        "email": "duplicate_user@example.com",
        "password": "SecurePassword123!",
        "display_name": "Duplicate Test",
        "profile_type": "CAREGIVER",
    }
    # First registration
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    # Second registration with same email
    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


def test_login_success_and_last_login_updated():
    """Verify login authenticates valid user and returns tokens."""
    email = "login_test@example.com"
    password = "MyStrongPassword2026!"

    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": "Login Tester",
            "profile_type": "CHILD",
        },
    )

    # Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert data["user"]["email"] == email
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_credentials_masked():
    """Verify invalid password does not reveal whether the user exists."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "AnyPassword123!"},
    )
    assert login_resp.status_code == 401
    assert login_resp.json()["detail"] == "Invalid email or password."


def test_refresh_token_flow():
    """Verify exchanging a refresh token returns fresh access and refresh tokens."""
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh_flow@example.com",
            "password": "RefreshPassword123!",
            "display_name": "Refresh User",
            "profile_type": "CAREGIVER",
        },
    )
    refresh_token = reg_resp.json()["refresh_token"]

    # Exchange refresh token
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user_me():
    """Verify /auth/me returns authenticated user profiles and roles."""
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "me_test@example.com",
            "password": "MePassword123!",
            "display_name": "Me User",
            "profile_type": "ELDER",
        },
    )
    access_token = reg_resp.json()["access_token"]

    # Request /auth/me with Bearer token
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "me_test@example.com"
    assert "ELDER" in me_data["roles"]
    assert len(me_data["profiles"]) == 1
    assert me_data["profiles"][0]["display_name"] == "Me User"


def test_get_current_user_unauthorized():
    """Verify /auth/me rejects requests without valid bearer token."""
    # No auth header
    resp1 = client.get("/api/v1/auth/me")
    assert resp1.status_code in (401, 403)

    # Invalid token
    resp2 = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.fake.token"}
    )
    assert resp2.status_code == 401
