# claimOS Persistence Architecture

```mermaid
graph TD
    API[FastAPI Endpoints] --> UOW[Unit of Work]
    UOW --> Repos[Repository Layer]
    
    Repos -->|Injects Memory Repository| Memory[Python Dict]
    Repos -->|Injects SQL Repository| SQLAlchemy[SQLAlchemy ORM]
    
    SQLAlchemy --> Postgres[(PostgreSQL)]
```

L'architecture est fondamentalement basée sur les principes du **Domain Driven Design (DDD)**.
Les endpoints n'interagissent jamais directement avec SQLAlchemy, mais toujours avec une interface abstraite de type `IRepository`.
Cela garantit une inversion de dépendance totale, et permet à claimOS de tourner indifféremment "In-Memory" ou "On-Disk" avec PostgreSQL.
