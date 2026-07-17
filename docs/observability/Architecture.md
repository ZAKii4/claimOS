# Architecture d'Observabilité & Télémétrie

```mermaid
graph TD
    Client[Next.js Client] --> Gateway[FastAPI]
    
    Gateway --> OpenTelemetry[Tracing Manager]
    Gateway --> Prometheus[Metrics Manager]
    Gateway --> Logger[JSON Logging]
    
    Prometheus --> Grafana[Dashboards]
    OpenTelemetry --> Jaeger[Trace UI]
    
    Gateway --> AIOps[AIOps Engine]
    AIOps --> Predictions[Anomaly & Capacity]
```

## Composants
- **Prometheus** : Expose `/api/v1/observability/metrics` pour un scraping externe.
- **OpenTelemetry** : Génère un `trace_id` unique qui est propagé dans tous les logs.
- **AIOps** : Une couche d'analyse prédictive qui évalue la santé des serveurs et remonte des anomalies (ex: Latence anormale ou VRAM surchargée).
