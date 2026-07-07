"""
Generic base repository implementing common CRUD operations.

Every domain-specific repository inherits from ``BaseRepository``
and can add specialised query methods.
"""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic repository providing CRUD operations for a SQLAlchemy model.

    Usage::

        class ClaimRepository(BaseRepository[ClaimFile]):
            def __init__(self, db: Session):
                super().__init__(ClaimFile, db)
    """

    def __init__(self, model: type[T], db: Session) -> None:
        self._model = model
        self._db = db

    # ── Read ─────────────────────────────────────────────────────────────

    def get_by_id(self, entity_id: UUID) -> T | None:
        """Return a single entity by primary key, or ``None``."""
        return self._db.get(self._model, entity_id)

    def get_all(self, *, skip: int = 0, limit: int = 20) -> list[T]:
        """Return a paginated list of entities."""
        stmt = select(self._model).offset(skip).limit(limit)
        return list(self._db.scalars(stmt).all())

    def count(self) -> int:
        """Return the total count of entities."""
        stmt = select(func.count()).select_from(self._model)
        result = self._db.execute(stmt).scalar_one()
        return result

    # ── Write ────────────────────────────────────────────────────────────

    def create(self, entity: T) -> T:
        """Persist a new entity and return it with its generated id."""
        self._db.add(entity)
        self._db.flush()
        self._db.refresh(entity)
        return entity

    def update(self, entity_id: UUID, data: dict) -> T | None:
        """
        Partially update an entity.

        Returns the updated entity, or ``None`` if not found.
        """
        entity = self.get_by_id(entity_id)
        if entity is None:
            return None
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        self._db.flush()
        self._db.refresh(entity)
        return entity

    def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by id. Returns ``True`` if it existed."""
        entity = self.get_by_id(entity_id)
        if entity is None:
            return False
        self._db.delete(entity)
        self._db.flush()
        return True
