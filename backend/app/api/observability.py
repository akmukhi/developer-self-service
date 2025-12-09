"""
Observability API endpoints (logs and metrics)
"""

import logging
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, Dict, Any, List
from app.services.logging_service import get_logging_service
from app.services.metrics_service import get_metrics_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/logs/{service_id}")
async def get_logs(
    service_id: str,
    lines: Optional[int] = Query(100, ge=1, le=10000, description="Number of lines to retrieve"),
    since_minutes: Optional[int] = Query(None, ge=1, description="Get logs since N minutes ago"),
    search: Optional[str] = Query(None, description="Search term to filter logs"),
    namespace: Optional[str] = Query(None, description="Override namespace (defaults to service namespace)")
) -> Dict[str, Any]:
    """
    Get logs for a service
    
    Service ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        logging_service = get_logging_service()
        
        # Parse service ID (format: namespace/name or just name)
        if "/" in service_id:
            svc_namespace, svc_name = service_id.split("/", 1)
        else:
            svc_namespace = namespace or "default"
            svc_name = service_id
        
        # Use provided namespace or service namespace
        target_namespace = namespace or svc_namespace
        
        # If search term provided, use search endpoint
        if search:
            logs_result = logging_service.search_logs(
                deployment_name=svc_name,
                namespace=target_namespace,
                search_term=search,
                tail_lines=lines or 1000,
                case_sensitive=False
            )
        elif since_minutes:
            # Get logs since specific time
            logs_result = logging_service.get_logs_since(
                deployment_name=svc_name,
                namespace=target_namespace,
                since_minutes=since_minutes
            )
        else:
            # Get tail of logs
            logs_result = logging_service.get_logs_tail(
                deployment_name=svc_name,
                namespace=target_namespace,
                lines=lines or 100
            )
        
        return {
            "service_id": service_id,
            "namespace": target_namespace,
            "deployment": svc_name,
            **logs_result
        }
        
    except Exception as e:
        logger.error(f"Failed to get logs for service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )


@router.get("/logs/{service_id}/aggregated")
async def get_aggregated_logs(
    service_id: str,
    lines: Optional[int] = Query(100, ge=1, le=10000, description="Number of lines to retrieve"),
    namespace: Optional[str] = Query(None, description="Override namespace")
) -> Dict[str, Any]:
    """
    Get aggregated logs for a service (all pods combined into single stream)
    
    Service ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        logging_service = get_logging_service()
        
        # Parse service ID
        if "/" in service_id:
            svc_namespace, svc_name = service_id.split("/", 1)
        else:
            svc_namespace = namespace or "default"
            svc_name = service_id
        
        target_namespace = namespace or svc_namespace
        
        # Get logs
        logs_result = logging_service.get_deployment_logs(
            deployment_name=svc_name,
            namespace=target_namespace,
            tail_lines=lines or 100
        )
        
        # Aggregate logs
        aggregated_logs = logging_service.aggregate_logs(logs_result, sort_by_time=True)
        
        return {
            "service_id": service_id,
            "namespace": target_namespace,
            "deployment": svc_name,
            "aggregated_logs": aggregated_logs,
            "total_pods": logs_result.get("total_pods", 0),
            "total_lines": logs_result.get("total_lines", 0),
            "retrieved_at": logs_result.get("retrieved_at")
        }
        
    except Exception as e:
        logger.error(f"Failed to get aggregated logs for service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get aggregated logs: {str(e)}"
        )


@router.get("/logs/{service_id}/statistics")
async def get_log_statistics(
    service_id: str,
    lines: Optional[int] = Query(1000, ge=1, le=10000, description="Number of lines to analyze"),
    namespace: Optional[str] = Query(None, description="Override namespace")
) -> Dict[str, Any]:
    """
    Get log statistics for a service (error counts, log levels, etc.)
    
    Service ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        logging_service = get_logging_service()
        
        # Parse service ID
        if "/" in service_id:
            svc_namespace, svc_name = service_id.split("/", 1)
        else:
            svc_namespace = namespace or "default"
            svc_name = service_id
        
        target_namespace = namespace or svc_namespace
        
        # Get statistics
        stats = logging_service.get_log_statistics(
            deployment_name=svc_name,
            namespace=target_namespace,
            tail_lines=lines or 1000
        )
        
        return {
            "service_id": service_id,
            "namespace": target_namespace,
            "deployment": svc_name,
            **stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get log statistics for service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log statistics: {str(e)}"
        )


@router.get("/metrics/{service_id}")
async def get_metrics(
    service_id: str,
    namespace: Optional[str] = Query(None, description="Override namespace")
) -> Dict[str, Any]:
    """
    Get metrics for a service
    
    Service ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        metrics_service = get_metrics_service()
        
        # Check if metrics are available
        availability = metrics_service.check_metrics_available()
        if not availability.get("available"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Metrics API not available: {availability.get('reason')}"
            )
        
        # Parse service ID
        if "/" in service_id:
            svc_namespace, svc_name = service_id.split("/", 1)
        else:
            svc_namespace = namespace or "default"
            svc_name = service_id
        
        target_namespace = namespace or svc_namespace
        
        # Get service metrics
        metrics = metrics_service.get_service_metrics(
            service_id=svc_name,
            namespace=target_namespace
        )
        
        return {
            "service_id": service_id,
            "namespace": target_namespace,
            **metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/metrics/{service_id}/summary")
async def get_metrics_summary(
    service_id: str,
    namespace: Optional[str] = Query(None, description="Override namespace")
) -> Dict[str, Any]:
    """
    Get a summary of metrics for a service
    
    Service ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        metrics_service = get_metrics_service()
        
        # Check if metrics are available
        availability = metrics_service.check_metrics_available()
        if not availability.get("available"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Metrics API not available: {availability.get('reason')}"
            )
        
        # Parse service ID
        if "/" in service_id:
            svc_namespace, svc_name = service_id.split("/", 1)
        else:
            svc_namespace = namespace or "default"
            svc_name = service_id
        
        target_namespace = namespace or svc_namespace
        
        # Get metrics summary
        summary = metrics_service.get_metrics_summary(
            deployment_name=svc_name,
            namespace=target_namespace
        )
        
        return {
            "service_id": service_id,
            "namespace": target_namespace,
            **summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics summary for service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics summary: {str(e)}"
        )


@router.get("/metrics/availability")
async def check_metrics_availability() -> Dict[str, Any]:
    """
    Check if metrics API is available
    """
    try:
        metrics_service = get_metrics_service()
        availability = metrics_service.check_metrics_available()
        
        return {
            "available": availability.get("available", False),
            "reason": availability.get("reason", "Unknown"),
            "timestamp": availability.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"Failed to check metrics availability: {e}")
        return {
            "available": False,
            "reason": f"Error checking availability: {str(e)}"
        }


@router.get("/deployments/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: str,
    lines: Optional[int] = Query(100, ge=1, le=10000, description="Number of lines to retrieve"),
    since_minutes: Optional[int] = Query(None, ge=1, description="Get logs since N minutes ago"),
    search: Optional[str] = Query(None, description="Search term to filter logs"),
    namespace: Optional[str] = Query(None, description="Override namespace")
) -> Dict[str, Any]:
    """
    Get logs for a deployment
    
    Deployment ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        logging_service = get_logging_service()
        
        # Parse deployment ID
        if "/" in deployment_id:
            dep_namespace, dep_name = deployment_id.split("/", 1)
        else:
            dep_namespace = namespace or "default"
            dep_name = deployment_id
        
        target_namespace = namespace or dep_namespace
        
        # If search term provided, use search endpoint
        if search:
            logs_result = logging_service.search_logs(
                deployment_name=dep_name,
                namespace=target_namespace,
                search_term=search,
                tail_lines=lines or 1000,
                case_sensitive=False
            )
        elif since_minutes:
            logs_result = logging_service.get_logs_since(
                deployment_name=dep_name,
                namespace=target_namespace,
                since_minutes=since_minutes
            )
        else:
            logs_result = logging_service.get_logs_tail(
                deployment_name=dep_name,
                namespace=target_namespace,
                lines=lines or 100
            )
        
        return {
            "deployment_id": deployment_id,
            "namespace": target_namespace,
            "deployment": dep_name,
            **logs_result
        }
        
    except Exception as e:
        logger.error(f"Failed to get logs for deployment {deployment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )


@router.get("/deployments/{deployment_id}/metrics")
async def get_deployment_metrics(
    deployment_id: str,
    namespace: Optional[str] = Query(None, description="Override namespace")
) -> Dict[str, Any]:
    """
    Get metrics for a deployment
    
    Deployment ID format: namespace/name or just name (defaults to 'default' namespace)
    """
    try:
        metrics_service = get_metrics_service()
        
        # Check if metrics are available
        availability = metrics_service.check_metrics_available()
        if not availability.get("available"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Metrics API not available: {availability.get('reason')}"
            )
        
        # Parse deployment ID
        if "/" in deployment_id:
            dep_namespace, dep_name = deployment_id.split("/", 1)
        else:
            dep_namespace = namespace or "default"
            dep_name = deployment_id
        
        target_namespace = namespace or dep_namespace
        
        # Get deployment metrics
        metrics = metrics_service.get_deployment_metrics(
            deployment_name=dep_name,
            namespace=target_namespace
        )
        
        return {
            "deployment_id": deployment_id,
            "namespace": target_namespace,
            "deployment": dep_name,
            **metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for deployment {deployment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )
