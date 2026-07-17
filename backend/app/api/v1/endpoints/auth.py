from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.v1.dependencies import get_auth_service, get_current_operator
from app.models.operator import Operator
from app.security.jwt_manager import jwt_manager
from app.security.mfa_engine import mfa_engine
from app.security.password_policy import password_policy
from app.security.session_manager import session_manager
from app.security.zero_trust import zero_trust_engine
from app.services.auth_service import AuthService

router = APIRouter()

@router.get("/me")
async def get_me(operator: Operator = Depends(get_current_operator)):
    """Returns the real, authenticated operator behind the caller's Bearer token."""
    return {
        "id": str(operator.id),
        "employee_id": operator.employee_id,
        "full_name": operator.full_name,
        "email": operator.email,
        "role": operator.role.code if operator.role else None,
    }

@router.post("/login")
async def login(
    payload: dict[str, Any],
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    email = payload.get("email")
    password = payload.get("password")
    device_id = payload.get("device_id", "unknown-device")
    ip_address = request.client.host if request.client else "unknown"

    operator = auth_service.get_operator_by_email(email)
    if not operator or not operator.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials or inactive account")

    operator_id = str(operator.id)

    if password_policy.is_locked_out(operator_id):
        raise HTTPException(
            status_code=429,
            detail="Account temporarily locked due to too many failed login attempts",
        )

    if not password or not auth_service.verify_password(operator, password):
        password_policy.record_failed_attempt(operator_id)
        raise HTTPException(status_code=401, detail="Invalid credentials or inactive account")

    password_policy.reset_failed_attempts(operator_id)

    # Zero Trust Check
    risk = zero_trust_engine.calculate_risk_score(operator_id, ip_address, device_id)
    if risk >= 80:
        # High risk requires immediate MFA or blocks
        return {"status": "mfa_required", "user_id": operator_id}

    # Standard Login Success
    session_id = session_manager.create_session(operator_id, device_id, ip_address)
    zero_trust_engine.register_device(operator_id, device_id)

    access_token = jwt_manager.create_access_token(operator_id, {"sid": session_id})
    refresh_token = jwt_manager.create_refresh_token(operator_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "risk_score": risk
    }

@router.post("/mfa/enroll")
async def enroll_mfa(
    payload: dict[str, Any],
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Generates and persists a real TOTP secret for an operator, returning a
    provisioning URI that can be scanned by any standard authenticator app
    (Google Authenticator, Authy, ...). This must be called before MFA can
    ever succeed for that operator — there is no default/shared code.
    """
    user_id = payload.get("user_id")
    operator = auth_service.get_operator_by_id(user_id) if user_id else None
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    secret = mfa_engine.generate_secret()
    auth_service.set_mfa_secret(operator, secret)
    provisioning_uri = mfa_engine.get_provisioning_uri(secret, operator.email)

    return {"status": "mfa_enrolled", "provisioning_uri": provisioning_uri}

@router.post("/mfa/verify")
async def verify_mfa(
    payload: dict[str, Any],
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = payload.get("user_id")
    code = payload.get("code")
    device_id = payload.get("device_id", "unknown-device")
    ip_address = request.client.host if request.client else "unknown"

    operator = auth_service.get_operator_by_id(user_id) if user_id else None
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    if not operator.mfa_secret:
        raise HTTPException(
            status_code=422,
            detail="MFA is not enrolled for this account — call /auth/mfa/enroll first",
        )

    if not code or not mfa_engine.verify_totp(operator.mfa_secret, code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")

    # MFA is the second half of login for high-risk sessions — completes the
    # same session/token issuance the standard login path does, rather than
    # leaving the caller authenticated-but-tokenless.
    operator_id = str(operator.id)
    session_id = session_manager.create_session(operator_id, device_id, ip_address)
    zero_trust_engine.register_device(operator_id, device_id)

    access_token = jwt_manager.create_access_token(operator_id, {"sid": session_id})
    refresh_token = jwt_manager.create_refresh_token(operator_id)

    return {
        "status": "mfa_success",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/logout")
async def logout(payload: dict[str, Any]):
    session_id = payload.get("session_id")
    if session_id:
        session_manager.revoke_session(session_id)
    return {"status": "logged_out"}
