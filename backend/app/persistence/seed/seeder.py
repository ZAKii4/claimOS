import asyncio
import os
import uuid

from app.persistence.base import Base
from app.persistence.database import AsyncSessionFactory, engine
from app.persistence.models.core_models import Role, Tenant, User
from app.security.password_policy import PasswordPolicyManager


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def seed_data():
    async with AsyncSessionFactory() as session:
        # Check if already seeded
        result = await session.execute(User.__table__.select().limit(1))
        if result.first():
            print("Database already seeded.")
            return

        print("Seeding database...")
        # 1. Create Tenant
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(id=tenant_id, name="ClaimOS Default Tenant")
        session.add(tenant)

        # 2. Create Role
        role_id = str(uuid.uuid4())
        role = Role(id=role_id, name="Admin", permissions=["*"])
        session.add(role)

        # 3. Create Admin User
        admin_password = os.environ.get("ADMIN_SEED_PASSWORD")
        if not admin_password:
            raise RuntimeError(
                "ADMIN_SEED_PASSWORD environment variable must be set to seed the admin user."
            )
        admin_id = str(uuid.uuid4())
        admin = User(
            id=admin_id,
            tenant_id=tenant_id,
            username="admin",
            email="admin@claimos.ai",
            hashed_password=PasswordPolicyManager().get_password_hash(admin_password),
        )
        session.add(admin)

        await session.commit()
        print("Database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(seed_data())
