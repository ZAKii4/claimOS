from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────────────
# Tenant
# ─────────────────────────────────────────────────────

class TenantIsolationStrategy(str, Enum):
    SHARED_SCHEMA = "SHARED_SCHEMA"
    DEDICATED_SCHEMA = "DEDICATED_SCHEMA"
    DEDICATED_DATABASE = "DEDICATED_DATABASE"


class Tenant(BaseModel):
    id: str
    name: str
    slug: str  # subdomain identifier
    isolation: TenantIsolationStrategy = TenantIsolationStrategy.SHARED_SCHEMA
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TenantContext(BaseModel):
    tenant_id: str
    organization_id: str = ""
    business_unit: str = ""
    environment: str = "production"
    user_id: str = ""


# ─────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────

class TenantConfig(BaseModel):
    tenant_id: str
    settings: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────
# Feature Flags
# ─────────────────────────────────────────────────────

class FeatureFlag(BaseModel):
    name: str
    enabled: bool = False
    tenant_overrides: Dict[str, bool] = Field(default_factory=dict)
    user_overrides: Dict[str, bool] = Field(default_factory=dict)
    rollout_percentage: float = 100.0  # 0-100


# ─────────────────────────────────────────────────────
# Plugin
# ─────────────────────────────────────────────────────

class PluginInfo(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    active: bool = True
    provides: List[str] = Field(default_factory=list)  # e.g. ["ocr_provider", "agent"]


# ─────────────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────────────

class TaskState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    DEAD = "DEAD"


class TaskEntry(BaseModel):
    id: str
    name: str
    tenant_id: str = ""
    priority: int = 0
    state: TaskState = TaskState.PENDING
    retries: int = 0
    max_retries: int = 3
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────
# Cluster
# ─────────────────────────────────────────────────────

class NodeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DRAINING = "DRAINING"
    DOWN = "DOWN"


class WorkerNode(BaseModel):
    id: str
    host: str
    port: int = 8000
    status: NodeStatus = NodeStatus.ACTIVE
    is_leader: bool = False
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    task_count: int = 0


class ScalingRecommendation(BaseModel):
    action: str  # "scale_out", "scale_in", "no_change"
    reason: str
    current_workers: int
    recommended_workers: int


# ─────────────────────────────────────────────────────
# Gateway
# ─────────────────────────────────────────────────────

class RateLimitEntry(BaseModel):
    tenant_id: str
    requests_count: int = 0
    window_start: float = 0.0
    limit: int = 100  # per minute


# ─────────────────────────────────────────────────────
# Backup
# ─────────────────────────────────────────────────────

class BackupEntry(BaseModel):
    id: str
    tenant_id: str = "global"
    backup_type: str = "snapshot"  # "snapshot", "incremental"
    data: Dict[str, Any] = Field(default_factory=dict)
    checksum: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────
# Billing
# ─────────────────────────────────────────────────────

class TenantUsage(BaseModel):
    tenant_id: str
    ocr_calls: int = 0
    llm_calls: int = 0
    storage_mb: float = 0.0
    claims_processed: int = 0
    total_cost: float = 0.0


# ─────────────────────────────────────────────────────
# Deployment
# ─────────────────────────────────────────────────────

class DeploymentMode(str, Enum):
    LOCAL = "LOCAL"
    DOCKER_COMPOSE = "DOCKER_COMPOSE"
    KUBERNETES = "KUBERNETES"
    ON_PREMISE = "ON_PREMISE"
    CLOUD = "CLOUD"
    HYBRID = "HYBRID"


class DeploymentStatus(BaseModel):
    mode: DeploymentMode
    healthy: bool = True
    services: Dict[str, str] = Field(default_factory=dict)
