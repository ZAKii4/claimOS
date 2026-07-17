"""
Operator (human reviewer) model.

Maps to the ``operator`` table from ``002_core_domain.sql``.
"""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Operator(TimestampMixin, Base):
    __tablename__ = "operator"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    employee_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operator_role.id"), nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    accuracy_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)

    # Auth: hashed with app.security.password_policy.PasswordPolicyManager (pbkdf2_sha256).
    # NULL means no password has been set yet — login must be refused, not silently allowed.
    hashed_password: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # Base32 TOTP secret, set via /auth/mfa/enroll. NULL means MFA is not enrolled.
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    role = relationship("OperatorRole", lazy="joined")
