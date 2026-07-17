import pytest
from app.security.jwt_manager import jwt_manager
from app.security.password_policy import password_policy
from app.security.mfa_engine import mfa_engine
from app.security.zero_trust import zero_trust_engine
from app.security.session_manager import session_manager
from app.security.api_keys import api_key_manager

def test_jwt_manager():
    token = jwt_manager.create_access_token("U1", {"role": "admin"})
    payload = jwt_manager.decode_token(token)
    assert payload is not None
    assert payload["sub"] == "U1"
    assert payload["role"] == "admin"
    
    # Revoke
    jwt_manager.revoke_token(token)
    assert jwt_manager.decode_token(token) is None

def test_password_policy():
    assert password_policy.is_complex_enough("weak") is False
    assert password_policy.is_complex_enough("StrongP@ss1") is True
    
    hash_pwd = password_policy.get_password_hash("StrongP@ss1")
    assert password_policy.verify_password("StrongP@ss1", hash_pwd) is True
    assert password_policy.verify_password("wrong", hash_pwd) is False

def test_brute_force():
    email = "hacker@test.com"
    for _ in range(5):
        password_policy.record_failed_attempt(email)
    
    assert password_policy.is_locked_out(email) is True
    password_policy.reset_failed_attempts(email)
    assert password_policy.is_locked_out(email) is False

def test_mfa():
    secret = mfa_engine.generate_secret()
    assert len(secret) == 32
    
    uri = mfa_engine.get_provisioning_uri(secret, "test@test.com")
    assert "test%40test.com" in uri
    assert "claimOS" in uri
    
    # We can't easily test the actual 6 digit code without pyotp generating it for us
    import pyotp
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    
    assert mfa_engine.verify_totp(secret, valid_code) is True
    assert mfa_engine.verify_totp(secret, "000000") is False

def test_zero_trust():
    user = "U1"
    device = "D1"
    
    # First time login from unknown device and bad IP -> High risk
    risk = zero_trust_engine.calculate_risk_score(user, "unknown", device)
    assert risk >= 90
    
    # Register device
    zero_trust_engine.register_device(user, device)
    
    # Login again from same device with known good IP
    risk2 = zero_trust_engine.calculate_risk_score(user, "192.168.1.1", device)
    assert risk2 < 50

def test_session_manager():
    u = "U1"
    s1 = session_manager.create_session(u, "iPhone", "1.1.1.1")
    s2 = session_manager.create_session(u, "Mac", "1.1.1.1")
    s3 = session_manager.create_session(u, "iPad", "1.1.1.1")
    
    assert len(session_manager.get_user_sessions(u)) == 3
    
    # Creating a 4th session should revoke the oldest (s1)
    import time
    time.sleep(0.01) # to ensure s4 is newer
    s4 = session_manager.create_session(u, "PC", "1.1.1.1")
    
    sessions = session_manager.get_user_sessions(u)
    assert len(sessions) == 3
    session_ids = [s["session_id"] for s in sessions]
    assert s4 in session_ids
    assert s1 not in session_ids

def test_api_keys():
    key = api_key_manager.generate_key("T1", "App1", ["read", "write"])
    assert key.startswith("cos_live_")
    
    data = api_key_manager.validate_key(key)
    assert data is not None
    assert data["tenant_id"] == "T1"
    
    api_key_manager.revoke_key(key)
    assert api_key_manager.validate_key(key) is None
