import abc
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

T = TypeVar("T")

class IRepository(Generic[T], abc.ABC):
    """Abstract base class for data access repositories."""
    @abc.abstractmethod
    async def get(self, id: str) -> Optional[T]:
        pass

    @abc.abstractmethod
    async def list(self) -> List[T]:
        pass

    @abc.abstractmethod
    async def create(self, item: T) -> T:
        pass

    @abc.abstractmethod
    async def update(self, item: T) -> T:
        pass

    @abc.abstractmethod
    async def delete(self, id: str) -> bool:
        pass

class SQLRepository(IRepository[T]):
    """SQLAlchemy implementation of the repository pattern."""
    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self.session = session
        self.model_class = model_class

    async def get(self, id: str) -> Optional[T]:
        return await self.session.get(self.model_class, id)

    async def list(self) -> List[T]:
        result = await self.session.execute(select(self.model_class))
        return list(result.scalars().all())

    async def create(self, item: T) -> T:
        self.session.add(item)
        await self.session.flush()
        return item

    async def update(self, item: T) -> T:
        # Assuming the item is already attached to the session and modified
        await self.session.flush()
        return item

    async def delete(self, id: str) -> bool:
        item = await self.get(id)
        if item:
            await self.session.delete(item)
            await self.session.flush()
            return True
        return False

class MemoryRepository(IRepository[T]):
    """In-Memory implementation of the repository pattern for fallback and testing."""
    def __init__(self):
        self._storage: Dict[str, T] = {}

    async def get(self, id: str) -> Optional[T]:
        return self._storage.get(id)

    async def list(self) -> List[T]:
        return list(self._storage.values())

    async def create(self, item: T) -> T:
        # Expecting items to have an 'id' attribute
        item_id = getattr(item, "id", None)
        if item_id is None:
            raise ValueError("Item must have an 'id' attribute")
        self._storage[item_id] = item
        return item

    async def update(self, item: T) -> T:
        item_id = getattr(item, "id", None)
        if item_id is None or item_id not in self._storage:
            raise ValueError("Item not found")
        self._storage[item_id] = item
        return item

    async def delete(self, id: str) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False
