"""
Service management API endpoints
"""

import logging
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from app.models.service import Service, ServiceCreate, ServiceStatus, ResourceRequirements
from app.services.kubernetes_service import get_kubernetes_service
from app.services.secrets_service import get_secrets_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=Service, status_code=status.HTTP_201_CREATED)
async def create_service(service_data: ServiceCreate) -> Service:
    """
    Create a new service
    
    This creates:
    - A Kubernetes Deployment
    - A Kubernetes Service
    - Default secrets for the service
    """
    try:
        k8s = get_kubernetes_service()
        secrets = get_secrets_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        # Validate service name (Kubernetes naming requirements)
        service_name = service_data.name.lower().replace("_", "-")
        if not service_name.replace("-", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service name must contain only alphanumeric characters and hyphens"
            )
        
        namespace = service_data.namespace or "default"
        
        # Prepare resource requirements
        resources_dict = None
        if service_data.resources:
            resources_dict = {
                "cpu": service_data.resources.cpu,
                "memory": service_data.resources.memory
            }
        
        # Create labels
        labels = {"app": service_name, "managed-by": "developer-self-service"}
        
        # Create Kubernetes Deployment
        try:
            deployment = k8s.create_deployment(
                name=service_name,
                image=service_data.image,
                namespace=namespace,
                replicas=service_data.replicas,
                env_vars=service_data.env_vars or {},
                ports=service_data.ports or [],
                resources=resources_dict,
                labels=labels
            )
            logger.info(f"Created deployment {service_name} in namespace {namespace}")
        except Exception as e:
            logger.error(f"Failed to create deployment: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create deployment: {str(e)}"
            )
        
        # Create Kubernetes Service (for networking)
        try:
            service_ports = []
            if service_data.ports:
                for port in service_data.ports:
                    service_ports.append({"port": port, "targetPort": port})
            else:
                service_ports = [{"port": 80, "targetPort": 80}]
            
            k8s_service = k8s.create_service(
                name=service_name,
                namespace=namespace,
                ports=service_ports,
                selector=labels,
                service_type="ClusterIP"
            )
            logger.info(f"Created service {service_name} in namespace {namespace}")
        except Exception as e:
            logger.warning(f"Failed to create Kubernetes service (deployment still created): {e}")
            # Don't fail if service creation fails, deployment is more important
        
        # Create default secrets for the service
        try:
            secrets.create_secret_for_service(
                service_id=service_name,
                namespace=namespace
            )
            logger.info(f"Created default secrets for service {service_name}")
        except Exception as e:
            logger.warning(f"Failed to create secrets (service still created): {e}")
            # Don't fail if secret creation fails
        
        # Get deployment status to determine service status
        deployment_info = k8s.get_deployment(service_name, namespace=namespace)
        
        # Map deployment status to service status
        deployment_status = deployment_info.get("status", "unknown")
        if deployment_status == "available":
            service_status = ServiceStatus.RUNNING
        elif deployment_status == "progressing":
            service_status = ServiceStatus.CREATING
        elif deployment_status == "failed":
            service_status = ServiceStatus.FAILED
        else:
            service_status = ServiceStatus.PENDING
        
        # Create service ID (namespace/name format)
        service_id = f"{namespace}/{service_name}"
        
        # Build response
        created_at = datetime.utcnow()
        if deployment_info.get("created_at"):
            try:
                created_at = datetime.fromisoformat(deployment_info["created_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        service = Service(
            id=service_id,
            name=service_name,
            image=service_data.image,
            replicas=service_data.replicas,
            namespace=namespace,
            status=service_status,
            resources=service_data.resources or ResourceRequirements(),
            env_vars=service_data.env_vars or {},
            ports=service_data.ports or [],
            created_at=created_at,
            updated_at=created_at,
            metadata={
                "deployment": deployment_info,
                "k8s_service": k8s_service if 'k8s_service' in locals() else None
            }
        )
        
        return service
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create service: {str(e)}"
        )


@router.get("", response_model=List[Service])
async def list_services(namespace: Optional[str] = None) -> List[Service]:
    """
    List all services
    
    Optionally filter by namespace
    """
    try:
        k8s = get_kubernetes_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        # Get all deployments
        deployments = k8s.list_deployments(namespace=namespace)
        
        services = []
        for deployment in deployments:
            # Filter for services managed by this portal (optional, or return all)
            # For MVP, we'll return all deployments as services
            
            deployment_status = deployment.get("status", "unknown")
            if deployment_status == "available":
                service_status = ServiceStatus.RUNNING
            elif deployment_status == "progressing":
                service_status = ServiceStatus.CREATING
            elif deployment_status == "failed":
                service_status = ServiceStatus.FAILED
            else:
                service_status = ServiceStatus.PENDING
            
            # Parse created_at
            created_at = datetime.utcnow()
            if deployment.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(deployment["created_at"].replace("Z", "+00:00"))
                except Exception:
                    pass
            
            service_id = deployment.get("id", f"{deployment.get('namespace', 'default')}/{deployment.get('name', 'unknown')}")
            
            # Get resource requirements from deployment (if available)
            # For MVP, we'll use defaults
            resources = ResourceRequirements()
            
            service = Service(
                id=service_id,
                name=deployment.get("name", "unknown"),
                image=deployment.get("image", ""),
                replicas=deployment.get("replicas", {}).get("desired", 1),
                namespace=deployment.get("namespace", "default"),
                status=service_status,
                resources=resources,
                env_vars={},  # Would need to query deployment spec to get this
                ports=[],  # Would need to query deployment spec to get this
                created_at=created_at,
                updated_at=created_at,
                metadata={"deployment": deployment}
            )
            
            services.append(service)
        
        return services
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list services: {str(e)}"
        )


@router.get("/{service_id}", response_model=Service)
async def get_service(service_id: str) -> Service:
    """
    Get service details by ID
    
    Service ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
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
        
        # Get deployment
        deployment = k8s.get_deployment(name=name, namespace=namespace)
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service {service_id} not found"
            )
        
        # Map deployment status to service status
        deployment_status = deployment.get("status", "unknown")
        if deployment_status == "available":
            service_status = ServiceStatus.RUNNING
        elif deployment_status == "progressing":
            service_status = ServiceStatus.CREATING
        elif deployment_status == "failed":
            service_status = ServiceStatus.FAILED
        else:
            service_status = ServiceStatus.PENDING
        
        # Parse timestamps
        created_at = datetime.utcnow()
        updated_at = None
        
        if deployment.get("created_at"):
            try:
                created_at = datetime.fromisoformat(deployment["created_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        # Get Kubernetes service info
        k8s_service = None
        try:
            k8s_service = k8s.get_service(name=name, namespace=namespace)
        except Exception:
            pass  # Service might not exist, that's okay
        
        # Get secret info
        secret_info = None
        try:
            secrets = get_secrets_service()
            secret_info = secrets.get_secret(f"{name}-secrets", namespace=namespace)
        except Exception:
            pass  # Secrets might not exist
        
        service_id_full = f"{namespace}/{name}"
        
        # Default resources (would need to query deployment spec for actual values)
        resources = ResourceRequirements()
        
        service = Service(
            id=service_id_full,
            name=name,
            image=deployment.get("image", ""),
            replicas=deployment.get("replicas", {}).get("desired", 1),
            namespace=namespace,
            status=service_status,
            resources=resources,
            env_vars={},  # Would need to query deployment spec
            ports=[],  # Would need to query deployment spec
            created_at=created_at,
            updated_at=updated_at,
            metadata={
                "deployment": deployment,
                "k8s_service": k8s_service,
                "secrets": secret_info
            }
        )
        
        return service
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service: {str(e)}"
        )
