"""
Service model definitions
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ServiceStatus(str, Enum):
    """Service status enumeration"""
    PENDING = "pending"
    CREATING = "creating"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"


class ResourceRequirements(BaseModel):
    """Resource requirements for a service"""
    cpu: Optional[str] = Field(default="100m", description="CPU request/limit")
    memory: Optional[str] = Field(default="128Mi", description="Memory request/limit")


class ServiceCreate(BaseModel):
    """Model for creating a new service"""
    name: str = Field(..., description="Service name", min_length=1, max_length=63)
    image: str = Field(..., description="Container image", min_length=1)
    replicas: int = Field(default=1, ge=1, le=100, description="Number of replicas")
    namespace: Optional[str] = Field(default="default", description="Kubernetes namespace")
    resources: Optional[ResourceRequirements] = Field(default_factory=ResourceRequirements, description="Resource requirements")
    env_vars: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables")
    ports: Optional[list[int]] = Field(default_factory=list, description="Container ports to expose")


class Service(BaseModel):
    """Service model"""
    id: str = Field(..., description="Service ID")
    name: str = Field(..., description="Service name")
    image: str = Field(..., description="Container image")
    replicas: int = Field(..., description="Number of replicas")
    namespace: str = Field(..., description="Kubernetes namespace")
    status: ServiceStatus = Field(..., description="Service status")
    resources: ResourceRequirements = Field(..., description="Resource requirements")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    ports: list[int] = Field(default_factory=list, description="Container ports")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "svc-123",
                "name": "my-service",
                "image": "nginx:latest",
                "replicas": 2,
                "namespace": "default",
                "status": "running",
                "resources": {
                    "cpu": "200m",
                    "memory": "256Mi"
                },
                "env_vars": {"ENV": "production"},
                "ports": [80, 443],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }

