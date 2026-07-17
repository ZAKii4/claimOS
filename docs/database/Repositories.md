# Repositories

L'interface `IRepository[T]` définit les opérations CRUD standard (create, get, list, update, delete).

## Implémentations
- **SQLRepository** : Utilise une session SQLAlchemy asynchrone (`AsyncSession`).
- **MemoryRepository** : Utilise un dictionnaire Python standard. Cette implémentation est utile pour les environnements de test où la rapidité d'exécution prévaut.

## Exemple d'injection
```python
# FastAPI Dependency
async def get_claim_repository(session: AsyncSession = Depends(get_db_session)) -> IRepository[Claim]:
    if USE_MEMORY_DB:
        return MemoryRepository()
    return SQLRepository(session, Claim)
```
