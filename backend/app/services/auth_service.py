"""
Auth service for real DB-backed authentication.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.operator import Operator
from app.security.password_policy import password_policy


class AuthService:
    def __init__(self, db: Session):
        self._db = db

    def get_operator_by_email(self, email: str) -> Operator | None:
        """Fetch operator by email."""
        stmt = select(Operator).where(Operator.email == email)
        return self._db.scalars(stmt).first()

    def get_operator_by_id(self, operator_id: str) -> Operator | None:
        """Fetch operator by id."""
        try:
            uuid_id = uuid.UUID(str(operator_id))
        except ValueError:
            return None
        return self._db.get(Operator, uuid_id)

    def verify_password(self, operator: Operator, plain_password: str) -> bool:
        """
        Verifies a plaintext password against the operator's stored hash.
        An operator with no hash set (hashed_password is None) can never
        authenticate — there is nothing to verify against.
        """
        if not operator.hashed_password:
            return False
        return password_policy.verify_password(plain_password, operator.hashed_password)

    def set_password(self, operator: Operator, plain_password: str) -> None:
        """Hashes and persists a new password for the operator."""
        operator.hashed_password = password_policy.get_password_hash(plain_password)
        self._db.commit()

    def set_mfa_secret(self, operator: Operator, secret: str) -> None:
        """Persists a newly-enrolled TOTP secret for the operator."""
        operator.mfa_secret = secret
        self._db.commit()
