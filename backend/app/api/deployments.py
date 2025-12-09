"""
Deployment management API endpoints
"""

import logging
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from app.models.deployment import Deployment, DeploymentStatus, PodStatus
from app.services.kubernetes_service import get_kubernetes_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[Deployment])
async def list_deployments(
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    service_id: Optional[str] = Query(None, description="Filter by service ID")
) -> List[Deployment]:
    """
    List all deployments
    
    Optionally filter by namespace or service ID
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
        
        deployment_list = []
        for deployment in deployments:
            # Filter by service_id if provided
            if service_id:
                # Service ID format: namespace/name
                if "/" in service_id:
                    svc_namespace, svc_name = service_id.split("/", 1)
                else:
                    svc_namespace = namespace or "default"
                    svc_name = service_id
                
                # Check if deployment matches service
                dep_namespace = deployment.get("namespace", "default")
                dep_name = deployment.get("name", "")
                
                if dep_namespace != svc_namespace or dep_name != svc_name:
                    continue
            
            # Map deployment status
            dep_status = deployment.get("status", "unknown")
            if dep_status == "available":
                deployment_status = DeploymentStatus.AVAILABLE
            elif dep_status == "progressing":
                deployment_status = DeploymentStatus.PROGRESSING
            elif dep_status == "failed":
                deployment_status = DeploymentStatus.FAILED
            elif dep_status == "pending":
                deployment_status = DeploymentStatus.PENDING
            else:
                deployment_status = DeploymentStatus.UNKNOWN
            
            # Parse image tag
            image = deployment.get("image", "")
            image_tag = None
            if ":" in image:
                image_tag = image.split(":")[-1]
            
            # Parse timestamps
            created_at = datetime.utcnow()
            updated_at = None
            
            if deployment.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(deployment["created_at"].replace("Z", "+00:00"))
                except Exception:
                    pass
            
            # Get replica information
            replicas_info = deployment.get("replicas", {})
            pod_status = PodStatus(
                ready=replicas_info.get("ready", 0),
                desired=replicas_info.get("desired", 0),
                available=replicas_info.get("available", 0),
                unavailable=replicas_info.get("unavailable", 0)
            )
            
            # Create service_id (namespace/name format)
            dep_namespace = deployment.get("namespace", "default")
            dep_name = deployment.get("name", "unknown")
            service_id = f"{dep_namespace}/{dep_name}"
            
            deployment_obj = Deployment(
                id=deployment.get("id", f"{dep_namespace}/{dep_name}"),
                service_id=service_id,
                name=dep_name,
                namespace=dep_namespace,
                image=image,
                image_tag=image_tag,
                status=deployment_status,
                replicas=pod_status,
                created_at=created_at,
                updated_at=updated_at,
                metadata={
                    "labels": deployment.get("labels", {}),
                    "raw_deployment": deployment
                }
            )
            
            deployment_list.append(deployment_obj)
        
        return deployment_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list deployments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list deployments: {str(e)}"
        )


@router.get("/{deployment_id}", response_model=Deployment)
async def get_deployment(deployment_id: str) -> Deployment:
    """
    Get deployment details by ID
    
    Deployment ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        k8s = get_kubernetes_service()
        
        if not k8s.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Not connected to Kubernetes cluster"
            )
        
        # Parse deployment ID (format: namespace/name or just name)
        if "/" in deployment_id:
            namespace, name = deployment_id.split("/", 1)
        else:
            namespace = "default"
            name = deployment_id
        
        # Get deployment
        deployment = k8s.get_deployment(name=name, namespace=namespace)
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment {deployment_id} not found"
            )
        
        # Map deployment status
        dep_status = deployment.get("status", "unknown")
        if dep_status == "available":
            deployment_status = DeploymentStatus.AVAILABLE
        elif dep_status == "progressing":
            deployment_status = DeploymentStatus.PROGRESSING
        elif dep_status == "failed":
            deployment_status = DeploymentStatus.FAILED
        elif dep_status == "pending":
            deployment_status = DeploymentStatus.PENDING
        else:
            deployment_status = DeploymentStatus.UNKNOWN
        
        # Parse image tag
        image = deployment.get("image", "")
        image_tag = None
        if ":" in image:
            image_tag = image.split(":")[-1]
        
        # Parse timestamps
        created_at = datetime.utcnow()
        updated_at = None
        
        if deployment.get("created_at"):
            try:
                created_at = datetime.fromisoformat(deployment["created_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        # Get replica information
        replicas_info = deployment.get("replicas", {})
        pod_status = PodStatus(
            ready=replicas_info.get("ready", 0),
            desired=replicas_info.get("desired", 0),
            available=replicas_info.get("available", 0),
            unavailable=replicas_info.get("unavailable", 0)
        )
        
        # Get pods for this deployment
        pods = []
        try:
            pods = k8s.get_pods(namespace=namespace, label_selector=f"app={name}")
        except Exception as e:
            logger.warning(f"Failed to get pods for deployment: {e}")
        
        # Get Kubernetes service info
        k8s_service = None
        try:
            k8s_service = k8s.get_service(name=name, namespace=namespace)
        except Exception:
            pass  # Service might not exist
        
        # Create service_id (namespace/name format)
        service_id = f"{namespace}/{name}"
        
        deployment_obj = Deployment(
            id=deployment_id if "/" in deployment_id else f"{namespace}/{name}",
            service_id=service_id,
            name=name,
            namespace=namespace,
            image=image,
            image_tag=image_tag,
            status=deployment_status,
            replicas=pod_status,
            created_at=created_at,
            updated_at=updated_at,
            metadata={
                "labels": deployment.get("labels", {}),
                "pods": [
                    {
                        "name": pod.get("name"),
                        "status": pod.get("status"),
                        "ready": pod.get("ready")
                    }
                    for pod in pods
                ],
                "k8s_service": k8s_service,
                "raw_deployment": deployment
            }
        )
        
        return deployment_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deployment: {str(e)}"
        )
