import pytest
from app.governance.models import User, Role, Permission, Policy, PolicyRule, PolicyDecision, RetentionPolicy
from app.governance.authorization.rbac import RBACEngine
from app.governance.authorization.abac import ABACEngine
from app.governance.policy.engine import PolicyEngine
from app.governance.pii.detector import PIIDetector
from app.governance.pii.masking import DataMaskingEngine
from app.governance.encryption.engine import EncryptionEngine
from app.governance.secrets.manager import SecretManager
from app.governance.audit.chain import AuditChain
from app.governance.compliance.engine import ComplianceEngine
from app.governance.retention.manager import RetentionManager


# ─────────────────────────────────────────────────────
# RBAC
# ─────────────────────────────────────────────────────

def test_rbac_permission_granted():
    admin_role = Role(name="admin", permissions=[
        Permission(resource="Claims", action="Read"),
        Permission(resource="Claims", action="Write"),
    ])
    user = User(id="u1", username="alice", roles=["admin"])

    RBACEngine.register_role(admin_role)
    RBACEngine.register_user(user)

    assert RBACEngine.has_permission("u1", "Claims", "Read") is True
    assert RBACEngine.has_permission("u1", "Claims", "Write") is True


def test_rbac_permission_denied():
    viewer_role = Role(name="viewer", permissions=[
        Permission(resource="Claims", action="Read"),
    ])
    user = User(id="u2", username="bob", roles=["viewer"])

    RBACEngine.register_role(viewer_role)
    RBACEngine.register_user(user)

    assert RBACEngine.has_permission("u2", "Claims", "Read") is True
    assert RBACEngine.has_permission("u2", "Claims", "Delete") is False


def test_rbac_inactive_user():
    user = User(id="u3", username="charlie", roles=["admin"], active=False)
    RBACEngine.register_user(user)
    assert RBACEngine.has_permission("u3", "Claims", "Read") is False


# ─────────────────────────────────────────────────────
# ABAC
# ─────────────────────────────────────────────────────

def test_abac_department_match():
    user = User(id="u4", username="diana", attributes={"department": "fraud", "clearance_level": 3})
    resource = {"department": "fraud", "required_level": 2}
    assert ABACEngine.evaluate(user, resource, "read") is True


def test_abac_department_mismatch():
    user = User(id="u5", username="eve", attributes={"department": "claims", "clearance_level": 3})
    resource = {"department": "fraud", "required_level": 2}
    assert ABACEngine.evaluate(user, resource, "read") is False


def test_abac_clearance_too_low():
    user = User(id="u6", username="frank", attributes={"department": "fraud", "clearance_level": 1})
    resource = {"department": "fraud", "required_level": 3}
    assert ABACEngine.evaluate(user, resource, "read") is False


# ─────────────────────────────────────────────────────
# Policy Engine
# ─────────────────────────────────────────────────────

def test_policy_engine():
    policy = Policy(id="pol1", name="High Value Claims", rules=[
        PolicyRule(condition="amount > 50000", decision=PolicyDecision.DENY, message="Requires manual approval"),
        PolicyRule(condition="amount <= 50000", decision=PolicyDecision.ALLOW),
    ])
    PolicyEngine.register_policy(policy)

    assert PolicyEngine.evaluate("pol1", {"amount": 100000}) == PolicyDecision.DENY
    assert PolicyEngine.evaluate("pol1", {"amount": 1000}) == PolicyDecision.ALLOW


# ─────────────────────────────────────────────────────
# PII Detection
# ─────────────────────────────────────────────────────

def test_pii_detect_email():
    detections = PIIDetector.scan("Contact alice@example.com for details")
    assert len(detections) == 1
    assert detections[0].pii_type == "email"
    assert detections[0].value == "alice@example.com"


def test_pii_detect_iban():
    detections = PIIDetector.scan("IBAN: FR7630006000011234567890189")
    assert any(d.pii_type == "iban" for d in detections)


def test_pii_detect_plate():
    detections = PIIDetector.scan("Vehicle plate: AB-123-CD")
    assert any(d.pii_type == "plate_fr" for d in detections)


def test_pii_contains():
    assert PIIDetector.contains_pii("Send to user@test.fr") is True
    assert PIIDetector.contains_pii("No personal data here") is False


# ─────────────────────────────────────────────────────
# Data Masking
# ─────────────────────────────────────────────────────

def test_mask_partial():
    assert DataMaskingEngine.mask("AB-123-CD", "partial") == "A*******D"


def test_mask_full():
    assert DataMaskingEngine.mask("secret", "full") == "******"


def test_mask_hash():
    result = DataMaskingEngine.mask("secret", "hash")
    assert len(result) == 64  # SHA-256 hex digest


def test_mask_tokenize():
    result = DataMaskingEngine.mask("secret", "tokenize")
    assert result.startswith("TOK_")


# ─────────────────────────────────────────────────────
# Encryption
# ─────────────────────────────────────────────────────

def test_encrypt_decrypt():
    key_id = EncryptionEngine.generate_key()
    ciphertext = EncryptionEngine.encrypt("Sensitive data", key_id)
    assert ciphertext != "Sensitive data"

    plaintext = EncryptionEngine.decrypt(ciphertext, key_id)
    assert plaintext == "Sensitive data"


def test_key_rotation():
    old_key = EncryptionEngine.generate_key()
    ciphertext = EncryptionEngine.encrypt("old secret", old_key)

    new_key = EncryptionEngine.rotate_key()
    assert new_key != old_key
    assert EncryptionEngine.get_active_key_id() == new_key

    # Old key still works for decryption
    plaintext = EncryptionEngine.decrypt(ciphertext, old_key)
    assert plaintext == "old secret"


# ─────────────────────────────────────────────────────
# Secret Manager
# ─────────────────────────────────────────────────────

def test_secret_manager():
    sm = SecretManager()
    sm.set_secret("API_KEY", "sk-12345")
    assert sm.get_secret("API_KEY") == "sk-12345"
    assert sm.get_secret("NONEXISTENT") is None


# ─────────────────────────────────────────────────────
# Audit Chain
# ─────────────────────────────────────────────────────

def test_audit_chain_integrity():
    # Reset chain for test isolation
    AuditChain._entries = []

    AuditChain.record("alice", "Claims.Read", "CLM-001")
    AuditChain.record("bob", "Review.Override", "CLM-001", {"reason": "Urgent"})
    AuditChain.record("system", "Decision.Approved", "CLM-001")

    assert len(AuditChain.get_entries()) == 3
    assert AuditChain.verify_chain() is True


def test_audit_chain_tamper_detection():
    AuditChain._entries = []

    AuditChain.record("alice", "Claims.Read")
    AuditChain.record("bob", "Claims.Write")

    # Tamper with the first entry
    AuditChain._entries[0].entry_hash = "TAMPERED"

    assert AuditChain.verify_chain() is False


# ─────────────────────────────────────────────────────
# Compliance
# ─────────────────────────────────────────────────────

def test_compliance_all_pass():
    ctx = {
        "pii_masked": True, "retention_policy_defined": True, "consent_recorded": True,
        "encryption_enabled": True, "rbac_enabled": True,
        "audit_enabled": True, "alerts_enabled": True,
    }
    checks = ComplianceEngine.evaluate_all(ctx)
    assert all(c.status.value in ["PASS"] for c in checks)


def test_compliance_failures():
    ctx = {"pii_masked": False, "encryption_enabled": False}
    checks = ComplianceEngine.evaluate_all(ctx)
    failed = [c for c in checks if c.status == "FAIL"]
    assert len(failed) > 0


# ─────────────────────────────────────────────────────
# Retention
# ─────────────────────────────────────────────────────

def test_retention_policy():
    policy = RetentionPolicy(document_type="medical_certificate", retention_days=365 * 10, legal_hold=True)
    RetentionManager.register_policy(policy)

    result = RetentionManager.compute_retention("doc1", "medical_certificate")
    assert result.legal_hold is True
    assert result.archive_date < result.expiration_date
    assert result.deletion_date > result.expiration_date
