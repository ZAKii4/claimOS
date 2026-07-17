# Migrations (Alembic)

Alembic assure la gestion des versions du schéma de base de données. Il est configuré de façon asynchrone pour utiliser `create_async_engine`.

## Autogénération
Pour créer une nouvelle migration :
```bash
poetry run alembic revision --autogenerate -m "Description de la migration"
```

## Application
Pour appliquer toutes les migrations :
```bash
poetry run alembic upgrade head
```

Le script `seeder.py` utilise l'engine pour invoquer `Base.metadata.create_all` pour les environnements locaux simplifiés.
