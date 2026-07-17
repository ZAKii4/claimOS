"""
Regression tests for the real, DB-backed authentication flow.

Prior to this, /auth/login fetched the submitted password and never checked
it against anything — any password succeeded for a known, active email — and
/auth/mfa/verify accepted a hardcoded "123456" code for any user. Neither
had any test coverage, which is exactly how that went unnoticed.
"""

import uuid

import pyotp
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_session_factory
from app.main import app
from app.models.lookups import OperatorRole
from app.models.operator import Operator
from app.security.password_policy import password_policy

client = TestClient(app)

TEST_PASSWORD = "Test-Password-123!"


@pytest.fixture
def real_operator():
    """Creates a real operator row with a real password hash, and cleans up after."""
    Session = get_session_factory()
    db = Session()
    try:
        role = db.query(OperatorRole).filter(OperatorRole.code == "TEST_ROLE").first()
        if not role:
            role = OperatorRole(code="TEST_ROLE")
            db.add(role)
            db.commit()
            db.refresh(role)

        operator = Operator(
            employee_id=f"TEST-{uuid.uuid4().hex[:8]}",
            full_name="Test Operator",
            email=f"test-{uuid.uuid4().hex[:8]}@example.com",
            role_id=role.id,
            hashed_password=password_policy.get_password_hash(TEST_PASSWORD),
        )
        db.add(operator)
        db.commit()
        db.refresh(operator)
        yield operator
    finally:
        db.query(Operator).filter(Operator.id == operator.id).delete()
        db.commit()
        db.close()


def test_login_rejects_wrong_password(real_operator):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": real_operator.email, "password": "definitely-wrong"},
    )
    assert response.status_code == 401


def test_login_rejects_operator_with_no_password_set():
    """An operator that has never had a password set must never be able to log in."""
    Session = get_session_factory()
    db = Session()
    try:
        role = db.query(OperatorRole).filter(OperatorRole.code == "TEST_ROLE").first()
        operator = Operator(
            employee_id=f"NOPASS-{uuid.uuid4().hex[:8]}",
            full_name="No Password Operator",
            email=f"nopass-{uuid.uuid4().hex[:8]}@example.com",
            role_id=role.id,
            hashed_password=None,
        )
        db.add(operator)
        db.commit()
        db.refresh(operator)
        email = operator.email
        operator_id = operator.id
    finally:
        db.close()

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "anything-at-all"},
        )
        assert response.status_code == 401
    finally:
        db2 = Session()
        db2.query(Operator).filter(Operator.id == operator_id).delete()
        db2.commit()
        db2.close()


def test_login_accepts_correct_password(real_operator):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": real_operator.email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_mfa_verify_rejects_hardcoded_bypass_code(real_operator):
    """The old hardcoded "123456" bypass must no longer work."""
    enroll = client.post(
        "/api/v1/auth/mfa/enroll", json={"user_id": str(real_operator.id)}
    )
    assert enroll.status_code == 200

    response = client.post(
        "/api/v1/auth/mfa/verify",
        json={"user_id": str(real_operator.id), "code": "123456"},
    )
    assert response.status_code == 401


def test_mfa_verify_accepts_real_totp_code(real_operator):
    enroll = client.post(
        "/api/v1/auth/mfa/enroll", json={"user_id": str(real_operator.id)}
    )
    assert enroll.status_code == 200
    provisioning_uri = enroll.json()["provisioning_uri"]
    secret = provisioning_uri.split("secret=")[1].split("&")[0]

    real_code = pyotp.TOTP(secret).now()
    response = client.post(
        "/api/v1/auth/mfa/verify",
        json={"user_id": str(real_operator.id), "code": real_code},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "mfa_success"
    assert "access_token" in body


def test_mfa_verify_fails_without_enrollment(real_operator):
    response = client.post(
        "/api/v1/auth/mfa/verify",
        json={"user_id": str(real_operator.id), "code": "000000"},
    )
    assert response.status_code == 422


def test_protected_endpoint_rejects_missing_token():
    """A JWT is issued at login but was never actually checked anywhere — verify it now is."""
    response = client.get("/api/v1/claims")
    assert response.status_code == 401


def test_protected_endpoint_rejects_garbage_token():
    response = client.get(
        "/api/v1/claims", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_protected_endpoint_accepts_real_token(real_operator):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": real_operator.email, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/claims", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_me_returns_the_real_authenticated_operator(real_operator):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": real_operator.email, "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == real_operator.email
    assert body["full_name"] == real_operator.full_name


def test_me_rejects_missing_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
