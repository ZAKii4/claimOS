# Transactions (Unit Of Work)

Le gestionnaire `UnitOfWork` englobe un bloc d'instructions de base de données.

## Fonctionnement
Lorsqu'il est utilisé comme un gestionnaire de contexte asynchrone (`async with uow:`), il effectue automatiquement :
- `begin()` à l'ouverture.
- `commit()` à la fermeture si aucune exception n'est levée.
- `rollback()` si une exception survient.

## Code
```python
uow = UnitOfWork(session_factory)
async with uow:
    repo = SQLRepository(uow.session, Tenant)
    await repo.create(Tenant(name="Nouveau Tenant"))
```
Cela garantit l'atomicité totale des opérations.
