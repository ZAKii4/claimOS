# AIOps & Capacity Forecasting

claimOS utilise une approche proactive pour sa stabilité.

Le module `aiops_engine.py` ingère les métriques en temps réel et applique des seuils d'alerte. 

## Anomalies Détectées
- **Latency Spikes** : Si une route API (ex: LLM Inference) prend 500% de plus de temps que la moyenne glissante.
- **VRAM Exhaustion** : Si l'orchestrateur GPU approche les 95% constants.

## Prédictions
- Le système calcule la croissance de l'espace disque (PostgreSQL/pgvector) et prédit combien de jours il reste avant saturation (Time to Exhaustion).
