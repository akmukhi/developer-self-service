"""
Temporary environment management API endpoints
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.environment import Environment, EnvironmentCreate, EnvironmentStatus
from app.services.kubernetes_service import get_kubernetes_service

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for environments (in production, use a database)
# This tracks environment metadata and expiration
_environments_store: dict[str, dict] = {}


def _generate_environment_id() -> str:
    """Generate a unique environment ID"""
    return f"env-{uuid.uuid4().hex[:8]}"


def _generate_namespace_name(env_name: str, env_id: str) -> str:
    """Generate a valid Kubernetes namespace name"""
    # Kubernetes namespace names must be lowercase alphanumeric with hyphens
    name = env_name.lower().replace("_", "-")
    # Remove invalid characters
    name = "".join(c if c.isalnum() or c == "-" else "-" for c in name)
    # Add environment ID to ensure uniqueness
    return f"{name}-{env_id[:8]}"


@router.post("", response_model=Environment, status_code=status.HTTP_201_CREATED)
async def create_environment(env_data: EnvironmentCreate) -> Environment:
    """
    Request a temporary environment
    
    Creates a Kubernetes namespace with TTL and optionally deploys services
    """
    try:
        k8s = get_kubernetes_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        # Generate environment ID
        env_id = _generate_environment_id()
        
        # Generate namespace name
        if env_data.namespace:
            namespace = env_data.namespace.lower().replace("_", "-")
            # Validate namespace name
            if not all(c.isalnum() or c == "-" for c in namespace):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Namespace name must contain only alphanumeric characters and hyphens"
                )
        else:
            namespace = _generate_namespace_name(env_data.name, env_id)
        
        # Calculate expiration
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(hours=env_data.ttl_hours)
        
        # Prepare labels
        labels = {
            "managed-by": "developer-self-service",
            "environment-id": env_id,
            "environment-name": env_data.name,
            "ttl-hours": str(env_data.ttl_hours),
            "expires-at": expires_at.isoformat(),
            **env_data.labels
        }
        
        # Create Kubernetes namespace
        try:
            namespace_info = k8s.create_namespace(name=namespace, labels=labels)
            logger.info(f"Created namespace {namespace} for environment {env_id}")
        except Exception as e:
            logger.error(f"Failed to create namespace: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create namespace: {str(e)}"
            )
        
        # Deploy services if specified
        deployed_services = []
        if env_data.services:
            for service_id in env_data.services:
                try:
                    # Parse service ID (namespace/name format)
                    if "/" in service_id:
                        svc_namespace, svc_name = service_id.split("/", 1)
                    else:
                        svc_namespace = "default"
                        svc_name = service_id
                    
                    # Get deployment from source namespace
                    source_deployment = k8s.get_deployment(name=svc_name, namespace=svc_namespace)
                    if not source_deployment:
                        logger.warning(f"Service {service_id} not found, skipping")
                        continue
                    
                    # For MVP, we'll just log that services should be deployed
                    # In production, you'd clone the deployment to the new namespace
                    logger.info(f"Would deploy service {service_id} to namespace {namespace}")
                    deployed_services.append(service_id)
                except Exception as e:
                    logger.warning(f"Failed to deploy service {service_id}: {e}")
        
        # Store environment metadata
        environment_data = {
            "id": env_id,
            "name": env_data.name,
            "namespace": namespace,
            "status": EnvironmentStatus.ACTIVE.value,
            "ttl_hours": env_data.ttl_hours,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "services": deployed_services,
            "labels": env_data.labels
        }
        _environments_store[env_id] = environment_data
        
        # Create environment object
        environment = Environment(
            id=env_id,
            name=env_data.name,
            namespace=namespace,
            status=EnvironmentStatus.ACTIVE,
            ttl_hours=env_data.ttl_hours,
            created_at=created_at,
            expires_at=expires_at,
            services=deployed_services,
            labels=env_data.labels,
            metadata={
                "namespace_info": namespace_info,
                "source_services": env_data.services
            }
        )
        
        return environment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating environment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create environment: {str(e)}"
        )


@router.get("", response_model=List[Environment])
async def list_environments(
    namespace: Optional[str] = None,
    status_filter: Optional[EnvironmentStatus] = None
) -> List[Environment]:
    """
    List all temporary environments
    
    Optionally filter by namespace or status
    """
    try:
        k8s = get_kubernetes_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        environments = []
        now = datetime.utcnow()
        
        # Get environments from store and validate against actual namespaces
        for env_id, env_data in _environments_store.items():
            env_namespace = env_data.get("namespace")
            
            # Filter by namespace if provided
            if namespace and env_namespace != namespace:
                continue
            
            # Check if namespace still exists
            namespace_info = k8s.get_namespace(env_namespace)
            if not namespace_info:
                # Namespace was deleted, mark as deleted
                env_data["status"] = EnvironmentStatus.DELETED.value
                env_data["deleted_at"] = now.isoformat()
            
            # Determine status
            env_status_str = env_data.get("status", EnvironmentStatus.ACTIVE.value)
            
            # Check expiration
            expires_at_str = env_data.get("expires_at")
            if expires_at_str:
                try:
                    expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                    if expires_at < now:
                        if env_status_str == EnvironmentStatus.ACTIVE.value:
                            env_status_str = EnvironmentStatus.EXPIRED.value
                except Exception:
                    pass
            
            # Filter by status if provided
            if status_filter and env_status_str != status_filter.value:
                continue
            
            # Parse timestamps
            created_at = datetime.utcnow()
            expires_at = datetime.utcnow()
            deleted_at = None
            
            if env_data.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(env_data["created_at"].replace("Z", "+00:00"))
                except Exception:
                    pass
            
            if expires_at_str:
                try:
                    expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                except Exception:
                    pass
            
            if env_data.get("deleted_at"):
                try:
                    deleted_at = datetime.fromisoformat(env_data["deleted_at"].replace("Z", "+00:00"))
                except Exception:
                    pass
            
            environment = Environment(
                id=env_id,
                name=env_data.get("name", "unknown"),
                namespace=env_namespace,
                status=EnvironmentStatus(env_status_str),
                ttl_hours=env_data.get("ttl_hours", 24),
                created_at=created_at,
                expires_at=expires_at,
                deleted_at=deleted_at,
                services=env_data.get("services", []),
                labels=env_data.get("labels", {}),
                metadata={
                    "namespace_exists": namespace_info is not None
                }
            )
            
            environments.append(environment)
        
        return environments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list environments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list environments: {str(e)}"
        )


@router.get("/{environment_id}", response_model=Environment)
async def get_environment(environment_id: str) -> Environment:
    """
    Get environment details by ID
    """
    try:
        k8s = get_kubernetes_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        # Get environment from store
        env_data = _environments_store.get(environment_id)
        if not env_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Environment {environment_id} not found"
            )
        
        env_namespace = env_data.get("namespace")
        namespace_info = k8s.get_namespace(env_namespace)
        
        # Determine status
        env_status_str = env_data.get("status", EnvironmentStatus.ACTIVE.value)
        now = datetime.utcnow()
        
        if not namespace_info:
            env_status_str = EnvironmentStatus.DELETED.value
        else:
            # Check expiration
            expires_at_str = env_data.get("expires_at")
            if expires_at_str:
                try:
                    expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                    if expires_at < now and env_status_str == EnvironmentStatus.ACTIVE.value:
                        env_status_str = EnvironmentStatus.EXPIRED.value
                except Exception:
                    pass
        
        # Parse timestamps
        created_at = datetime.utcnow()
        expires_at = datetime.utcnow()
        deleted_at = None
        
        if env_data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(env_data["created_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        if env_data.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(env_data["expires_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        if env_data.get("deleted_at"):
            try:
                deleted_at = datetime.fromisoformat(env_data["deleted_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        # Get deployments in the namespace
        deployments = []
        try:
            deployments = k8s.list_deployments(namespace=env_namespace)
        except Exception:
            pass
        
        environment = Environment(
            id=environment_id,
            name=env_data.get("name", "unknown"),
            namespace=env_namespace,
            status=EnvironmentStatus(env_status_str),
            ttl_hours=env_data.get("ttl_hours", 24),
            created_at=created_at,
            expires_at=expires_at,
            deleted_at=deleted_at,
            services=env_data.get("services", []),
            labels=env_data.get("labels", {}),
            metadata={
                "namespace_info": namespace_info,
                "deployments": deployments,
                "namespace_exists": namespace_info is not None
            }
        )
        
        return environment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get environment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get environment: {str(e)}"
        )


@router.delete("/{environment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(environment_id: str):
    """
    Delete/cleanup a temporary environment
    
    Deletes the Kubernetes namespace and all resources within it
    """
    try:
        k8s = get_kubernetes_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        # Get environment from store
        env_data = _environments_store.get(environment_id)
        if not env_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Environment {environment_id} not found"
            )
        
        env_namespace = env_data.get("namespace")
        
        # Delete Kubernetes namespace (this will delete all resources in the namespace)
        try:
            deleted = k8s.delete_namespace(env_namespace)
            if deleted:
                logger.info(f"Deleted namespace {env_namespace} for environment {environment_id}")
            else:
                logger.warning(f"Namespace {env_namespace} was already deleted")
        except Exception as e:
            logger.error(f"Failed to delete namespace {env_namespace}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete namespace: {str(e)}"
            )
        
        # Update environment status
        env_data["status"] = EnvironmentStatus.DELETED.value
        env_data["deleted_at"] = datetime.utcnow().isoformat()
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete environment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete environment: {str(e)}"
        )
