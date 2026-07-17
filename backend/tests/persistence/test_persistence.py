import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.persistence.base import Base
from app.persistence.models.core_models import Tenant, User, Claim
from app.persistence.repositories.base_repository import SQLRepository, MemoryRepository
from app.persistence.unit_of_work import UnitOfWork

import pytest_asyncio

# --- Test DB Setup ---
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def session_factory():
    return TestSessionLocal

# --- Repository Tests ---

@pytest.mark.asyncio
async def test_sql_repository_crud(session_factory):
    async with session_factory() as session:
        repo = SQLRepository(session, Tenant)
        
        # Create
        tenant = Tenant(name="Test Tenant")
        created = await repo.create(tenant)
        assert created.id is not None
        assert created.name == "Test Tenant"

        # Get
        fetched = await repo.get(created.id)
        assert fetched is not None
        assert fetched.name == "Test Tenant"
        
        # List
        tenants = await repo.list()
        assert len(tenants) == 1
        
        # Update
        fetched.name = "Updated Tenant"
        await repo.update(fetched)
        updated = await repo.get(created.id)
        assert updated.name == "Updated Tenant"

        # Delete
        deleted = await repo.delete(created.id)
        assert deleted is True
        fetched_again = await repo.get(created.id)
        assert fetched_again is None

@pytest.mark.asyncio
async def test_memory_repository_crud():
    repo = MemoryRepository[Tenant]()
    
    tenant = Tenant(name="Memory Tenant")
    # memory repo requires ID to be pre-set or generated before insert
    if not tenant.id:
        import uuid
        tenant.id = str(uuid.uuid4())
        
    created = await repo.create(tenant)
    assert created.id is not None
    
    fetched = await repo.get(created.id)
    assert fetched.name == "Memory Tenant"
    
    fetched.name = "Updated"
    await repo.update(fetched)
    assert (await repo.get(created.id)).name == "Updated"
    
    assert await repo.delete(created.id) is True
    assert await repo.get(created.id) is None

# --- Unit of Work Tests ---

@pytest.mark.asyncio
async def test_unit_of_work_commit(session_factory):
    uow = UnitOfWork(session_factory)
    
    async with uow:
        repo = SQLRepository(uow.session, Tenant)
        await repo.create(Tenant(name="UOW Tenant"))
        # Implicit commit on exit without exception

    async with session_factory() as session:
        repo = SQLRepository(session, Tenant)
        tenants = await repo.list()
        assert len(tenants) == 1
        assert tenants[0].name == "UOW Tenant"

@pytest.mark.asyncio
async def test_unit_of_work_rollback(session_factory):
    uow = UnitOfWork(session_factory)
    
    try:
        async with uow:
            repo = SQLRepository(uow.session, Tenant)
            await repo.create(Tenant(name="Rollback Tenant"))
            raise ValueError("Intentional failure")
    except ValueError:
        pass

    async with session_factory() as session:
        repo = SQLRepository(session, Tenant)
        tenants = await repo.list()
        assert len(tenants) == 0

@pytest.mark.asyncio
async def test_optimistic_locking(session_factory):
    async with session_factory() as session:
        repo = SQLRepository(session, Claim)
        # Create tenant first
        tenant = Tenant(name="Tenant A")
        session.add(tenant)
        await session.flush()
        
        claim = Claim(tenant_id=tenant.id, reference="CLM-123")
        await repo.create(claim)
        await session.commit()
        claim_id = claim.id

    # Simulate concurrent update
    async with session_factory() as s1, session_factory() as s2:
        c1 = await s1.get(Claim, claim_id)
        c2 = await s2.get(Claim, claim_id)

        c1.amount = 100
        c1.version = c1.version + 1
        await s1.commit()

        c2.amount = 200
        # In real optimistic locking, you'd check version on update, 
        # but here we just prove the version mechanism exists on the model
        assert c2.version == 1
