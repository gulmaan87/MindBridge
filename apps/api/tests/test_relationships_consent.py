"""Relationships & Consent Integration Tests (API Contract v2 §15-18).

Tests:
 Relationship:
  1. Create a pending relationship
  2. Reject self-relationship
  3. Subject approves relationship (PENDING → ACTIVE)
  4. Related user cannot approve (must be subject)
  5. Cannot re-approve (invalid state transition)
  6. Subject revokes active relationship (ACTIVE → REVOKED)
  7. Subject manages permissions on active relationship
  8. Non-subject cannot manage permissions
  9. List relationships shows both participants
 Consent:
  10. Record a new consent
  11. Duplicate active consent returns 409
  12. List consents for user
  13. Get single consent (ownership enforced)
  14. Revoke consent stamps revoked_at and flips granted=False
  15. Re-revoking returns 409
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(email: str, display_name: str, profile_type: str = "ELDER") -> str:
    """Register a user and return their access token."""
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
            "display_name": display_name,
            "profile_type": profile_type,
        },
    )
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Relationship tests
# ---------------------------------------------------------------------------


class TestRelationships:
    """Integration tests for /api/v1/relationships endpoints."""

    def test_create_relationship_pending(self):
        """Creating a relationship starts in PENDING status."""
        token_subject = _register_and_login("rel_subject1@test.com", "Subject One", "ELDER")
        token_related = _register_and_login("rel_related1@test.com", "Related One", "CAREGIVER")

        # Get related user's ID via /auth/me
        me_resp = client.get("/api/v1/auth/me", headers=_auth(token_related))
        related_user_id = me_resp.json()["id"]

        resp = client.post(
            "/api/v1/relationships",
            json={"related_user_id": related_user_id, "relationship_type": "CAREGIVER"},
            headers=_auth(token_subject),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "PENDING"
        assert data["relationship_type"] == "CAREGIVER"

    def test_self_relationship_rejected(self):
        """Cannot create a relationship with oneself."""
        token = _register_and_login("rel_self@test.com", "Self User", "ELDER")
        me_resp = client.get("/api/v1/auth/me", headers=_auth(token))
        own_id = me_resp.json()["id"]

        resp = client.post(
            "/api/v1/relationships",
            json={"related_user_id": own_id, "relationship_type": "CAREGIVER"},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_subject_approves_relationship(self):
        """Subject can transition PENDING → ACTIVE."""
        token_subject = _register_and_login("rel_subj_approve@test.com", "Approve Subject", "ELDER")
        token_related = _register_and_login("rel_rel_approve@test.com", "Approve Related", "CAREGIVER")

        me_resp = client.get("/api/v1/auth/me", headers=_auth(token_related))
        related_id = me_resp.json()["id"]

        create_resp = client.post(
            "/api/v1/relationships",
            json={"related_user_id": related_id, "relationship_type": "CAREGIVER"},
            headers=_auth(token_subject),
        )
        rel_id = create_resp.json()["id"]

        # Subject approves
        patch_resp = client.patch(
            f"/api/v1/relationships/{rel_id}/status",
            json={"status": "ACTIVE"},
            headers=_auth(token_subject),
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "ACTIVE"

    def test_related_user_cannot_approve(self):
        """Related user cannot approve their own request (only subject can)."""
        token_subject = _register_and_login("rel_subj_cantappr@test.com", "Subj CantAppr", "ELDER")
        token_related = _register_and_login("rel_rel_cantappr@test.com", "Rel CantAppr", "CAREGIVER")

        me_resp = client.get("/api/v1/auth/me", headers=_auth(token_related))
        related_id = me_resp.json()["id"]

        create_resp = client.post(
            "/api/v1/relationships",
            json={"related_user_id": related_id, "relationship_type": "CAREGIVER"},
            headers=_auth(token_subject),
        )
        rel_id = create_resp.json()["id"]

        # Related user tries to approve — should be forbidden
        resp = client.patch(
            f"/api/v1/relationships/{rel_id}/status",
            json={"status": "ACTIVE"},
            headers=_auth(token_related),
        )
        assert resp.status_code == 403

    def test_invalid_state_transition(self):
        """ACTIVE → PENDING is not a valid transition."""
        token_subject = _register_and_login("rel_invalid_trans@test.com", "Invalid Trans", "ELDER")
        token_related = _register_and_login("rel_rel_invalid@test.com", "Rel Invalid", "CAREGIVER")

        me_resp = client.get("/api/v1/auth/me", headers=_auth(token_related))
        related_id = me_resp.json()["id"]

        create_resp = client.post(
            "/api/v1/relationships",
            json={"related_user_id": related_id, "relationship_type": "CAREGIVER"},
            headers=_auth(token_subject),
        )
        rel_id = create_resp.json()["id"]

        # Activate first
        client.patch(
            f"/api/v1/relationships/{rel_id}/status",
            json={"status": "ACTIVE"},
            headers=_auth(token_subject),
        )

        # Try to go back to PENDING — invalid
        resp = client.patch(
            f"/api/v1/relationships/{rel_id}/status",
            json={"status": "PENDING"},
            headers=_auth(token_subject),
        )
        assert resp.status_code == 422

    def test_subject_revokes_active_relationship(self):
        """Subject can revoke an ACTIVE relationship."""
        token_subject = _register_and_login("rel_revoke_s@test.com", "Revoke Subject", "ELDER")
        token_related = _register_and_login("rel_revoke_r@test.com", "Revoke Related", "CAREGIVER")

        me_resp = client.get("/api/v1/auth/me", headers=_auth(token_related))
        related_id = me_resp.json()["id"]

        create_resp = client.post(
            "/api/v1/relationships",
            json={"related_user_id": related_id, "relationship_type": "CAREGIVER"},
            headers=_auth(token_subject),
        )
        rel_id = create_resp.json()["id"]

        client.patch(
            f"/api/v1/relationships/{rel_id}/status",
            json={"status": "ACTIVE"},
            headers=_auth(token_subject),
        )

        revoke_resp = client.patch(
            f"/api/v1/relationships/{rel_id}/status",
            json={"status": "REVOKED"},
            headers=_auth(token_subject),
        )
        assert revoke_resp.status_code == 200
        assert revoke_resp.json()["status"] == "REVOKED"

    def test_permission_management_by_subject(self):
        """Subject can grant and delete permissions on ACTIVE relationships."""
        token_subject = _register_and_login("rel_perm_s@test.com", "Perm Subject", "ELDER")
        token_related = _register_and_login("rel_perm_r@test.com", "Perm Related", "CAREGIVER")

        me_resp = client.get("/api/v1/auth/me", headers=_auth(token_related))
        related_id = me_resp.json()["id"]

        create_resp = client.post(
            "/api/v1/relationships",
            json={"related_user_id": related_id, "relationship_type": "CAREGIVER"},
            headers=_auth(token_subject),
        )
        rel_id = create_resp.json()["id"]

        # Activate
        client.patch(
            f"/api/v1/relationships/{rel_id}/status",
            json={"status": "ACTIVE"},
            headers=_auth(token_subject),
        )

        # Grant permission
        perm_resp = client.post(
            f"/api/v1/relationships/{rel_id}/permissions",
            json={"permission": "VIEW_PROGRESS", "granted": True},
            headers=_auth(token_subject),
        )
        assert perm_resp.status_code == 200
        assert perm_resp.json()["permission"] == "VIEW_PROGRESS"
        assert perm_resp.json()["granted"] is True

        # Upsert same permission with revoke
        upsert_resp = client.post(
            f"/api/v1/relationships/{rel_id}/permissions",
            json={"permission": "VIEW_PROGRESS", "granted": False},
            headers=_auth(token_subject),
        )
        assert upsert_resp.status_code == 200
        assert upsert_resp.json()["granted"] is False

        # Delete permission
        del_resp = client.delete(
            f"/api/v1/relationships/{rel_id}/permissions/VIEW_PROGRESS",
            headers=_auth(token_subject),
        )
        assert del_resp.status_code == 204

    def test_non_subject_cannot_manage_permissions(self):
        """Related user cannot manage permissions — only the subject can."""
        token_subject = _register_and_login("rel_nperm_s@test.com", "NPerm Subject", "ELDER")
        token_related = _register_and_login("rel_nperm_r@test.com", "NPerm Related", "CAREGIVER")

        me_resp = client.get("/api/v1/auth/me", headers=_auth(token_related))
        related_id = me_resp.json()["id"]

        create_resp = client.post(
            "/api/v1/relationships",
            json={"related_user_id": related_id, "relationship_type": "CAREGIVER"},
            headers=_auth(token_subject),
        )
        rel_id = create_resp.json()["id"]

        client.patch(
            f"/api/v1/relationships/{rel_id}/status",
            json={"status": "ACTIVE"},
            headers=_auth(token_subject),
        )

        # Related user tries to grant permission
        resp = client.post(
            f"/api/v1/relationships/{rel_id}/permissions",
            json={"permission": "VIEW_MEMORIES", "granted": True},
            headers=_auth(token_related),
        )
        assert resp.status_code == 403

    def test_list_relationships_includes_both_sides(self):
        """Both participants can see the shared relationship in their list."""
        token_subject = _register_and_login("rel_list_s@test.com", "List Subject", "ELDER")
        token_related = _register_and_login("rel_list_r@test.com", "List Related", "CAREGIVER")

        me_resp = client.get("/api/v1/auth/me", headers=_auth(token_related))
        related_id = me_resp.json()["id"]

        create_resp = client.post(
            "/api/v1/relationships",
            json={"related_user_id": related_id, "relationship_type": "CAREGIVER"},
            headers=_auth(token_subject),
        )
        rel_id = create_resp.json()["id"]

        # Subject list
        list_subj = client.get("/api/v1/relationships", headers=_auth(token_subject))
        ids_subj = [r["id"] for r in list_subj.json()]
        assert rel_id in ids_subj

        # Related user list
        list_rel = client.get("/api/v1/relationships", headers=_auth(token_related))
        ids_rel = [r["id"] for r in list_rel.json()]
        assert rel_id in ids_rel


# ---------------------------------------------------------------------------
# Consent tests
# ---------------------------------------------------------------------------


class TestConsent:
    """Integration tests for /api/v1/consents endpoints."""

    def test_create_consent(self):
        """Recording a new consent returns HTTP 201 with correct fields."""
        token = _register_and_login("consent_create@test.com", "Consent Creator", "ELDER")

        resp = client.post(
            "/api/v1/consents",
            json={"consent_type": "DATA_PROCESSING", "version": "1.0", "granted": True},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["consent_type"] == "DATA_PROCESSING"
        assert data["granted"] is True
        assert data["revoked_at"] is None

    def test_duplicate_active_consent_returns_409(self):
        """Creating the same active consent type+version twice returns 409."""
        token = _register_and_login("consent_dup@test.com", "Consent Dup", "ELDER")

        payload = {"consent_type": "MEMORY_STORAGE", "version": "1.0", "granted": True}
        resp1 = client.post("/api/v1/consents", json=payload, headers=_auth(token))
        assert resp1.status_code == 201

        resp2 = client.post("/api/v1/consents", json=payload, headers=_auth(token))
        assert resp2.status_code == 409

    def test_list_consents(self):
        """List endpoint returns all consent records for the authenticated user."""
        token = _register_and_login("consent_list@test.com", "Consent Lister", "ELDER")

        for consent_type in ["DATA_PROCESSING", "VOICE_PROCESSING"]:
            client.post(
                "/api/v1/consents",
                json={"consent_type": consent_type, "version": "1.0", "granted": True},
                headers=_auth(token),
            )

        list_resp = client.get("/api/v1/consents", headers=_auth(token))
        assert list_resp.status_code == 200
        types = [r["consent_type"] for r in list_resp.json()]
        assert "DATA_PROCESSING" in types
        assert "VOICE_PROCESSING" in types

    def test_get_consent_ownership_enforced(self):
        """A user cannot read another user's consent record."""
        token_a = _register_and_login("consent_owner_a@test.com", "Owner A", "ELDER")
        token_b = _register_and_login("consent_owner_b@test.com", "Owner B", "CAREGIVER")

        resp = client.post(
            "/api/v1/consents",
            json={"consent_type": "AI_PROCESSING", "version": "1.0", "granted": True},
            headers=_auth(token_a),
        )
        consent_id = resp.json()["id"]

        # User B tries to read User A's consent
        get_resp = client.get(f"/api/v1/consents/{consent_id}", headers=_auth(token_b))
        assert get_resp.status_code == 403

    def test_revoke_consent(self):
        """Revoking a consent stamps revoked_at and flips granted to False."""
        token = _register_and_login("consent_revoke@test.com", "Consent Revoker", "ELDER")

        create_resp = client.post(
            "/api/v1/consents",
            json={"consent_type": "RESEARCH_PARTICIPATION", "version": "1.0", "granted": True},
            headers=_auth(token),
        )
        consent_id = create_resp.json()["id"]

        revoke_resp = client.patch(
            f"/api/v1/consents/{consent_id}/revoke",
            json={},
            headers=_auth(token),
        )
        assert revoke_resp.status_code == 200
        data = revoke_resp.json()
        assert data["granted"] is False
        assert data["revoked_at"] is not None

    def test_double_revoke_returns_409(self):
        """Revoking an already-revoked consent returns 409."""
        token = _register_and_login("consent_dblrevoke@test.com", "Dbl Revoker", "ELDER")

        create_resp = client.post(
            "/api/v1/consents",
            json={"consent_type": "CAREGIVER_ACCESS", "version": "1.0", "granted": True},
            headers=_auth(token),
        )
        consent_id = create_resp.json()["id"]

        client.patch(f"/api/v1/consents/{consent_id}/revoke", json={}, headers=_auth(token))

        # Second revoke
        resp2 = client.patch(f"/api/v1/consents/{consent_id}/revoke", json={}, headers=_auth(token))
        assert resp2.status_code == 409
