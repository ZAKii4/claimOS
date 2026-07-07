from app.platform.tenant.models import DeploymentMode, DeploymentStatus


class DeploymentManager:
    """Generates deployment manifests and manages deployment status."""

    _mode: DeploymentMode = DeploymentMode.LOCAL
    _status: DeploymentStatus = DeploymentStatus(mode=DeploymentMode.LOCAL)

    @classmethod
    def set_mode(cls, mode: DeploymentMode):
        cls._mode = mode
        cls._status = DeploymentStatus(mode=mode)

    @classmethod
    def get_status(cls) -> DeploymentStatus:
        return cls._status

    @classmethod
    def generate_dockerfile(cls) -> str:
        return """FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    @classmethod
    def generate_docker_compose(cls) -> str:
        return """version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/claimos
    depends_on:
      - db
  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=claimos
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
"""

    @classmethod
    def generate_k8s_deployment(cls) -> str:
        return """apiVersion: apps/v1
kind: Deployment
metadata:
  name: claimos-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: claimos
  template:
    metadata:
      labels:
        app: claimos
    spec:
      containers:
        - name: api
          image: claimos:latest
          ports:
            - containerPort: 8000
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "2Gi"
---
apiVersion: v1
kind: Service
metadata:
  name: claimos-api
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8000
  selector:
    app: claimos
"""

    @classmethod
    def generate_helm_values(cls) -> str:
        return """replicaCount: 3
image:
  repository: claimos
  tag: latest
service:
  type: LoadBalancer
  port: 80
resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 2Gi
postgresql:
  enabled: true
"""
