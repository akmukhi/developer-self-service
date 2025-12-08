"""
Deployment model definitions
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DeploymentStatus(str, Enum):
    """Deployment status enumeration"""
    PENDING = "pending"
    PROGRESSING = "progressing"
    AVAILABLE = "available"
    FAILED = "failed"
    UNKNOWN = "unknown"


class PodStatus(BaseModel):
    """Pod status information"""
    ready: int = Field(..., description="Number of ready pods")
    desired: int = Field(..., description="Desired number of pods")
    available: int = Field(..., description="Number of available pods")
    unavailable: int = Field(default=0, description="Number of unavailable pods")


class Deployment(BaseModel):
    """Deployment model"""
    id: str = Field(..., description="Deployment ID")
    service_id: str = Field(..., description="Associated service ID")
    name: str = Field(..., description="Deployment name")
    namespace: str = Field(..., description="Kubernetes namespace")
    image: str = Field(..., description="Container image")
    image_tag: Optional[str] = Field(default=None, description="Image tag/version")
    status: DeploymentStatus = Field(..., description="Deployment status")
    replicas: PodStatus = Field(..., description="Pod replica status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "deploy-123",
                "service_id": "svc-123",
                "name": "my-service-deployment",
                "namespace": "default",
                "image": "nginx:latest",
                "image_tag": "latest",
                "status": "available",
                "replicas": {
                    "ready": 2,
                    "desired": 2,
                    "available": 2,
                    "unavailable": 0
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }

