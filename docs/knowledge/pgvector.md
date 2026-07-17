# pgvector & Vector Database

L'extension `pgvector` transforme PostgreSQL en une puissante base de données vectorielle.

## Modèles
L'ORM SQLAlchemy a été étendu avec `Vector(768)` pour stocker les embeddings générés (par `nomic-embed` ou `bge-m3`).

## Recherche
Le `VectorRepository` effectue les calculs de similarité cosinus (Cosine Similarity) et supporte l'isolation multi-tenant pour garantir qu'un Tenant ne puisse jamais chercher dans les documents vectorisés d'un autre.
