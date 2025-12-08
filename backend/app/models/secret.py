"""
Secret model definitions
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SecretType(str, Enum):
    """Secret type enumeration"""
    OPAQUE = "Opaque"
    TLS = "kubernetes.io/tls"
    DOCKER_CONFIG = "kubernetes.io/dockerconfigjson"
    BASIC_AUTH = "kubernetes.io/basic-auth"
    SSH_AUTH = "kubernetes.io/ssh-auth"


class SecretRotationHistory(BaseModel):
    """Secret rotation history entry"""
    rotated_at: datetime = Field(..., description="Rotation timestamp")
    rotated_by: Optional[str] = Field(default=None, description="Who/what triggered the rotation")
    version: str = Field(..., description="Secret version identifier")


class Secret(BaseModel):
    """Secret model (does not include actual secret values)"""
    id: str = Field(..., description="Secret ID")
    service_id: str = Field(..., description="Associated service ID")
    name: str = Field(..., description="Secret name")
    namespace: str = Field(..., description="Kubernetes namespace")
    secret_type: SecretType = Field(default=SecretType.OPAQUE, description="Secret type")
    keys: List[str] = Field(default_factory=list, description="List of secret keys (not values)")
    last_rotated: Optional[datetime] = Field(default=None, description="Last rotation timestamp")
    rotation_history: List[SecretRotationHistory] = Field(default_factory=list, description="Rotation history")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "secret-123",
                "service_id": "svc-123",
                "name": "my-service-secrets",
                "namespace": "default",
                "secret_type": "Opaque",
                "keys": ["database_url", "api_key"],
                "last_rotated": "2024-01-01T12:00:00Z",
                "rotation_history": [
                    {
                        "rotated_at": "2024-01-01T12:00:00Z",
                        "rotated_by": "system",
                        "version": "v2"
                    }
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }


class SecretRotateRequest(BaseModel):
    """Request model for secret rotation"""
    keys: Optional[List[str]] = Field(default=None, description="Specific keys to rotate (all if not specified)")
    generate_new: bool = Field(default=True, description="Generate new secret values")
    update_deployments: bool = Field(default=True, description="Update deployments to use new secrets")

