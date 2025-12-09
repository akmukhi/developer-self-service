"""
Secret management API endpoints
"""

import logging
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from app.models.secret import Secret, SecretRotateRequest, SecretType, SecretRotationHistory
from app.services.secrets_service import get_secrets_service
from app.services.kubernetes_service import get_kubernetes_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{service_id}/rotate", response_model=Secret)
async def rotate_secrets(
    service_id: str,
    rotate_request: Optional[SecretRotateRequest] = None
) -> Secret:
    """
    Rotate secrets for a service
    
    Service ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        secrets = get_secrets_service()
        k8s = get_kubernetes_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        # Parse service ID (format: namespace/name or just name)
        if "/" in service_id:
            namespace, name = service_id.split("/", 1)
        else:
            namespace = "default"
            name = service_id
        
        # Default rotation request if not provided
        if rotate_request is None:
            rotate_request = SecretRotateRequest()
        
        # Determine secret name (defaults to {service_name}-secrets)
        secret_name = f"{name}-secrets"
        
        # Check if secret exists
        existing_secret = secrets.get_secret(secret_name, namespace=namespace)
        if not existing_secret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Secret {secret_name} not found for service {service_id}"
            )
        
        # Rotate the secret
        try:
            rotation_result = secrets.rotate_service_secrets(
                service_id=name,
                secret_name=secret_name,
                namespace=namespace,
                keys=rotate_request.keys,
                update_deployments=rotate_request.update_deployments
            )
        except Exception as e:
            logger.error(f"Failed to rotate secrets: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to rotate secrets: {str(e)}"
            )
        
        # Get updated secret information
        updated_secret_info = secrets.get_secret(secret_name, namespace=namespace)
        
        # Get rotation history
        rotation_history_list = secrets.get_secret_rotation_history(secret_name, namespace=namespace)
        
        # Add current rotation to history
        rotation_entry = SecretRotationHistory(
            rotated_at=datetime.utcnow(),
            rotated_by="api",
            version=f"v{len(rotation_history_list) + 1}"
        )
        rotation_history_list.append(rotation_entry)
        
        # Parse timestamps
        created_at = datetime.utcnow()
        if updated_secret_info.get("created_at"):
            try:
                created_at = datetime.fromisoformat(updated_secret_info["created_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        # Determine secret type
        secret_type_str = updated_secret_info.get("type", "Opaque")
        try:
            secret_type = SecretType(secret_type_str)
        except ValueError:
            secret_type = SecretType.OPAQUE
        
        # Build response
        secret = Secret(
            id=f"{namespace}/{secret_name}",
            service_id=service_id,
            name=secret_name,
            namespace=namespace,
            secret_type=secret_type,
            keys=updated_secret_info.get("keys", []),
            last_rotated=datetime.utcnow(),
            rotation_history=rotation_history_list,
            created_at=created_at,
            updated_at=datetime.utcnow(),
            metadata={
                "rotation_result": rotation_result,
                "rotated_keys": rotation_result.get("rotation", {}).get("rotated_keys", []),
                "deployments_updated": rotation_result.get("deployments_updated", False)
            }
        )
        
        logger.info(f"Rotated secrets for service {service_id}")
        return secret
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error rotating secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate secrets: {str(e)}"
        )


@router.get("/{service_id}", response_model=Secret)
async def get_secrets(service_id: str) -> Secret:
    """
    Get secret information for a service (metadata only, not values)
    
    Service ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        secrets = get_secrets_service()
        k8s = get_kubernetes_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        # Parse service ID (format: namespace/name or just name)
        if "/" in service_id:
            namespace, name = service_id.split("/", 1)
        else:
            namespace = "default"
            name = service_id
        
        # Determine secret name (defaults to {service_name}-secrets)
        secret_name = f"{name}-secrets"
        
        # Get secret information
        secret_info = secrets.get_secret(secret_name, namespace=namespace)
        
        if not secret_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Secret {secret_name} not found for service {service_id}"
            )
        
        # Get rotation history
        rotation_history_list = secrets.get_secret_rotation_history(secret_name, namespace=namespace)
        
        # Parse timestamps
        created_at = datetime.utcnow()
        last_rotated = None
        
        if secret_info.get("created_at"):
            try:
                created_at = datetime.fromisoformat(secret_info["created_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        # Get last rotation from history if available
        if rotation_history_list:
            last_rotated = rotation_history_list[-1].rotated_at
        
        # Determine secret type
        secret_type_str = secret_info.get("type", "Opaque")
        try:
            secret_type = SecretType(secret_type_str)
        except ValueError:
            secret_type = SecretType.OPAQUE
        
        # Build response
        secret = Secret(
            id=f"{namespace}/{secret_name}",
            service_id=service_id,
            name=secret_name,
            namespace=namespace,
            secret_type=secret_type,
            keys=secret_info.get("keys", []),
            last_rotated=last_rotated,
            rotation_history=rotation_history_list,
            created_at=created_at,
            updated_at=last_rotated or created_at,
            metadata={
                "secret_exists": True
            }
        )
        
        return secret
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get secrets: {str(e)}"
        )


@router.get("", response_model=List[Secret])
async def list_secrets(
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    service_id: Optional[str] = Query(None, description="Filter by service ID")
) -> List[Secret]:
    """
    List all secrets
    
    Optionally filter by namespace or service ID
    """
    try:
        secrets = get_secrets_service()
        k8s = get_kubernetes_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        # Get secrets
        if namespace:
            secrets_list = secrets.list_secrets(namespace=namespace)
        else:
            # List from all namespaces (for MVP, we'll use default)
            secrets_list = secrets.list_secrets(namespace="default")
            # In production, you'd iterate through all namespaces
        
        secret_objects = []
        for secret_info in secrets_list:
            secret_namespace = secret_info.get("namespace", "default")
            secret_name = secret_info.get("name", "")
            
            # Filter by service_id if provided
            if service_id:
                # Extract service name from service_id
                if "/" in service_id:
                    svc_namespace, svc_name = service_id.split("/", 1)
                else:
                    svc_namespace = "default"
                    svc_name = service_id
                
                # Check if secret name matches service pattern
                expected_secret_name = f"{svc_name}-secrets"
                if secret_name != expected_secret_name or secret_namespace != svc_namespace:
                    continue
            
            # Get rotation history
            rotation_history_list = secrets.get_secret_rotation_history(secret_name, secret_namespace)
            
            # Parse timestamps
            created_at = datetime.utcnow()
            last_rotated = None
            
            if secret_info.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(secret_info["created_at"].replace("Z", "+00:00"))
                except Exception:
                    pass
            
            if rotation_history_list:
                last_rotated = rotation_history_list[-1].rotated_at
            
            # Determine secret type
            secret_type_str = secret_info.get("type", "Opaque")
            try:
                secret_type = SecretType(secret_type_str)
            except ValueError:
                secret_type = SecretType.OPAQUE
            
            # Try to infer service_id from secret name
            inferred_service_id = secret_name.replace("-secrets", "")
            if secret_namespace != "default":
                inferred_service_id = f"{secret_namespace}/{inferred_service_id}"
            
            secret = Secret(
                id=f"{secret_namespace}/{secret_name}",
                service_id=inferred_service_id,
                name=secret_name,
                namespace=secret_namespace,
                secret_type=secret_type,
                keys=secret_info.get("keys", []),
                last_rotated=last_rotated,
                rotation_history=rotation_history_list,
                created_at=created_at,
                updated_at=last_rotated or created_at,
                metadata={}
            )
            
            secret_objects.append(secret)
        
        return secret_objects
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list secrets: {str(e)}"
        )


@router.get("/{service_id}/history", response_model=List[SecretRotationHistory])
async def get_rotation_history(service_id: str) -> List[SecretRotationHistory]:
    """
    Get rotation history for a service's secrets
    
    Service ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        secrets = get_secrets_service()
        k8s = get_kubernetes_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        # Parse service ID (format: namespace/name or just name)
        if "/" in service_id:
            namespace, name = service_id.split("/", 1)
        else:
            namespace = "default"
            name = service_id
        
        # Determine secret name
        secret_name = f"{name}-secrets"
        
        # Check if secret exists
        secret_info = secrets.get_secret(secret_name, namespace=namespace)
        if not secret_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Secret {secret_name} not found for service {service_id}"
            )
        
        # Get rotation history
        rotation_history = secrets.get_secret_rotation_history(secret_name, namespace=namespace)
        
        return rotation_history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rotation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rotation history: {str(e)}"
        )
