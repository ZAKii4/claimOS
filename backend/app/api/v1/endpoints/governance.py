from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from app.governance.authorization.rbac import RBACEngine
from app.governance.policy.engine import PolicyEngine
from app.governance.pii.detector import PIIDetector
from app.governance.pii.masking import DataMaskingEngine
from app.governance.encryption.engine import EncryptionEngine
from app.governance.audit.chain import AuditChain
from app.governance.compliance.engine import ComplianceEngine
from app.governance.retention.manager import RetentionManager

router = APIRouter(prefix="/governance", tags=["Enterprise Governance & Security"])


class ScanPIIRequest(BaseModel):
    text: str


class MaskRequest(BaseModel):
    value: str
    strategy: str = "partial"


class EncryptRequest(BaseModel):
    plaintext: str


class ComplianceRequest(BaseModel):
    context: Dict[str, Any]


@router.get("/users")
def list_users():
    return [u.model_dump() for u in RBACEngine.get_all_users()]


@router.get("/roles")
def list_roles():
    return [r.model_dump() for r in RBACEngine.get_all_roles()]


@router.get("/policies")
def list_policies():
    return [p.model_dump() for p in PolicyEngine.get_all_policies()]


@router.get("/audit")
def get_audit():
    return [e.model_dump() for e in AuditChain.get_entries()]


@router.post("/scan/pii")
def scan_pii(req: ScanPIIRequest):
    detections = PIIDetector.scan(req.text)
    return [d.model_dump() for d in detections]


@router.post("/mask")
def mask_data(req: MaskRequest):
    return {"masked": DataMaskingEngine.mask(req.value, req.strategy)}


@router.post("/encrypt")
def encrypt_data(req: EncryptRequest):
    key_id = EncryptionEngine.get_active_key_id()
    if not key_id:
        key_id = EncryptionEngine.generate_key()
    ciphertext = EncryptionEngine.encrypt(req.plaintext, key_id)
    return {"ciphertext": ciphertext, "key_id": key_id}


@router.post("/decrypt")
def decrypt_data(ciphertext: str, key_id: str):
    plaintext = EncryptionEngine.decrypt(ciphertext, key_id)
    return {"plaintext": plaintext}


@router.get("/compliance")
def check_compliance(req: ComplianceRequest):
    checks = ComplianceEngine.evaluate_all(req.context)
    return [c.model_dump() for c in checks]


@router.get("/retention")
def get_retention_policies():
    return [p.model_dump() for p in RetentionManager.get_policies()]
