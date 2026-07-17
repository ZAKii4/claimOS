import asyncio

from app.core.database import get_session_factory
from app.models.lookups import OperatorRole
from app.models.operator import Operator
from app.security.password_policy import password_policy

# Demo credential for local evaluation only — rotate before any real deployment.
DEFAULT_ADMIN_EMAIL = "admin@claimos.com"
DEFAULT_ADMIN_PASSWORD = "ClaimOS!Demo2026"

async def seed_operator():
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        # Create role if missing
        role = db.query(OperatorRole).filter(OperatorRole.code == "SUPER_ADMIN").first()
        if not role:
            role = OperatorRole(code="SUPER_ADMIN")
            db.add(role)
            db.commit()
            db.refresh(role)

        # Create operator if missing
        op = db.query(Operator).filter(Operator.email == DEFAULT_ADMIN_EMAIL).first()
        if not op:
            op = Operator(
                employee_id="ADM-001",
                full_name="System Administrator",
                email=DEFAULT_ADMIN_EMAIL,
                role_id=role.id,
                hashed_password=password_policy.get_password_hash(DEFAULT_ADMIN_PASSWORD),
            )
            db.add(op)
            db.commit()
            print(f"Successfully seeded {DEFAULT_ADMIN_EMAIL} operator.")
        else:
            # Idempotent: make sure the demo account always has a working
            # password, even if it was seeded before this field existed.
            op.hashed_password = password_policy.get_password_hash(DEFAULT_ADMIN_PASSWORD)
            db.commit()
            print(f"Operator {DEFAULT_ADMIN_EMAIL} already exists — password (re)set.")

        print(f"Login with: email={DEFAULT_ADMIN_EMAIL}  password={DEFAULT_ADMIN_PASSWORD}")
        print("This is a demo credential — rotate it before any real deployment.")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed_operator())
