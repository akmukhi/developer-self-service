"""
Environment model definitions
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class EnvironmentStatus(str, Enum):
    """Environment status enumeration"""
    CREATING = "creating"
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    DELETED = "deleted"


class EnvironmentCreate(BaseModel):
    """Model for creating a temporary environment"""
    name: str = Field(..., description="Environment name", min_length=1, max_length=63)
    ttl_hours: int = Field(default=24, ge=1, le=168, description="Time to live in hours (max 7 days)")
    namespace: Optional[str] = Field(default=None, description="Custom namespace (auto-generated if not provided)")
    services: Optional[List[str]] = Field(default_factory=list, description="List of service IDs to deploy in this environment")
    labels: Optional[Dict[str, str]] = Field(default_factory=dict, description="Additional labels")


class Environment(BaseModel):
    """Temporary environment model"""
    id: str = Field(..., description="Environment ID")
    name: str = Field(..., description="Environment name")
    namespace: str = Field(..., description="Kubernetes namespace")
    status: EnvironmentStatus = Field(..., description="Environment status")
    ttl_hours: int = Field(..., description="Time to live in hours")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    deleted_at: Optional[datetime] = Field(default=None, description="Deletion timestamp")
    services: List[str] = Field(default_factory=list, description="Service IDs in this environment")
    labels: Dict[str, str] = Field(default_factory=dict, description="Environment labels")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "env-123",
                "name": "dev-test-env",
                "namespace": "dev-test-env-123",
                "status": "active",
                "ttl_hours": 24,
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": "2024-01-02T00:00:00Z",
                "services": ["svc-123", "svc-456"],
                "labels": {"purpose": "testing", "team": "backend"}
            }
        }

