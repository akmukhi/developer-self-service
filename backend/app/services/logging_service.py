"""
Logging service
Handles fetching and aggregating pod logs from Kubernetes
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.services.kubernetes_service import get_kubernetes_service

logger = logging.getLogger(__name__)


class LoggingService:
    """Service for fetching and managing pod logs"""

    def __init__(self):
        """Initialize logging service"""
        self.kubernetes = get_kubernetes_service()

    def get_pod_logs(
        self,
        pod_name: str,
        namespace: str = "default",
        container: Optional[str] = None,
        tail_lines: Optional[int] = None,
        since_seconds: Optional[int] = None,
        previous: bool = False
    ) -> Dict[str, Any]:
        """
        Get logs from a specific pod
        
        Args:
            pod_name: Pod name
            namespace: Kubernetes namespace
            container: Container name (if pod has multiple containers)
            tail_lines: Number of lines to retrieve from the end
            since_seconds: Retrieve logs since N seconds ago
            previous: Get logs from previous container instance
            
        Returns:
            Dictionary with pod logs and metadata
        """
        try:
            logs = self.kubernetes.get_pod_logs(
                pod_name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
                since_seconds=since_seconds
            )
            
            return {
                "pod": pod_name,
                "namespace": namespace,
                "container": container,
                "logs": logs,
                "lines": len(logs.split("\n")) if logs else 0,
                "retrieved_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get logs for pod {pod_name}: {e}")
            raise Exception(f"Failed to get pod logs: {str(e)}")

    def get_deployment_logs(
        self,
        deployment_name: str,
        namespace: str = "default",
        tail_lines: int = 100,
        since_seconds: Optional[int] = None,
        container: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get logs from all pods in a deployment
        
        Args:
            deployment_name: Deployment name
            namespace: Kubernetes namespace
            tail_lines: Number of lines per pod
            since_seconds: Retrieve logs since N seconds ago
            container: Container name (if pods have multiple containers)
            
        Returns:
            Dictionary with aggregated logs from all pods
        """
        try:
            # Get all pods for the deployment
            pods = self.kubernetes.get_pods(
                namespace=namespace,
                label_selector=f"app={deployment_name}"
            )
            
            if not pods:
                # Try alternative label selector
                pods = self.kubernetes.get_pods(
                    namespace=namespace,
                    label_selector=f"app.kubernetes.io/name={deployment_name}"
                )
            
            if not pods:
                logger.warning(f"No pods found for deployment {deployment_name} in namespace {namespace}")
                return {
                    "deployment": deployment_name,
                    "namespace": namespace,
                    "pods": [],
                    "total_lines": 0,
                    "retrieved_at": datetime.utcnow().isoformat()
                }
            
            # Get logs from each pod
            pod_logs = []
            total_lines = 0
            
            for pod in pods:
                pod_name = pod.get("name")
                if not pod_name:
                    continue
                
                try:
                    logs = self.kubernetes.get_pod_logs(
                        pod_name=pod_name,
                        namespace=namespace,
                        container=container,
                        tail_lines=tail_lines,
                        since_seconds=since_seconds
                    )
                    
                    log_lines = logs.split("\n") if logs else []
                    total_lines += len(log_lines)
                    
                    pod_logs.append({
                        "pod": pod_name,
                        "status": pod.get("status"),
                        "ready": pod.get("ready", False),
                        "logs": logs,
                        "lines": len(log_lines),
                        "retrieved_at": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Failed to get logs for pod {pod_name}: {e}")
                    pod_logs.append({
                        "pod": pod_name,
                        "status": pod.get("status"),
                        "ready": pod.get("ready", False),
                        "logs": f"Error retrieving logs: {str(e)}",
                        "lines": 0,
                        "error": str(e)
                    })
            
            return {
                "deployment": deployment_name,
                "namespace": namespace,
                "pods": pod_logs,
                "total_pods": len(pods),
                "total_lines": total_lines,
                "retrieved_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get deployment logs: {e}")
            raise Exception(f"Failed to get deployment logs: {str(e)}")

    def get_service_logs(
        self,
        service_id: str,
        namespace: str = "default",
        tail_lines: int = 100,
        since_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get logs for a service (finds deployment by service ID)
        
        Args:
            service_id: Service identifier
            namespace: Kubernetes namespace
            tail_lines: Number of lines per pod
            since_seconds: Retrieve logs since N seconds ago
            
        Returns:
            Dictionary with service logs
        """
        try:
            # Try to find deployment by service ID
            # In a real implementation, you'd have a mapping of service_id to deployment
            # For MVP, we'll assume service_id matches deployment name or use a label
            
            # First, try service_id as deployment name
            try:
                return self.get_deployment_logs(
                    deployment_name=service_id,
                    namespace=namespace,
                    tail_lines=tail_lines,
                    since_seconds=since_seconds
                )
            except Exception:
                pass
            
            # Try to find by label
            pods = self.kubernetes.get_pods(
                namespace=namespace,
                label_selector=f"service={service_id}"
            )
            
            if not pods:
                raise Exception(f"No pods found for service {service_id}")
            
            # Aggregate logs from all pods
            pod_logs = []
            total_lines = 0
            
            for pod in pods:
                pod_name = pod.get("name")
                if not pod_name:
                    continue
                
                try:
                    logs = self.kubernetes.get_pod_logs(
                        pod_name=pod_name,
                        namespace=namespace,
                        tail_lines=tail_lines,
                        since_seconds=since_seconds
                    )
                    
                    log_lines = logs.split("\n") if logs else []
                    total_lines += len(log_lines)
                    
                    pod_logs.append({
                        "pod": pod_name,
                        "status": pod.get("status"),
                        "logs": logs,
                        "lines": len(log_lines)
                    })
                except Exception as e:
                    logger.warning(f"Failed to get logs for pod {pod_name}: {e}")
                    pod_logs.append({
                        "pod": pod_name,
                        "status": pod.get("status"),
                        "logs": f"Error: {str(e)}",
                        "lines": 0
                    })
            
            return {
                "service_id": service_id,
                "namespace": namespace,
                "pods": pod_logs,
                "total_pods": len(pods),
                "total_lines": total_lines,
                "retrieved_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get service logs: {e}")
            raise Exception(f"Failed to get service logs: {str(e)}")

    def search_logs(
        self,
        deployment_name: str,
        namespace: str = "default",
        search_term: str = "",
        tail_lines: int = 1000,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Search logs for a specific term
        
        Args:
            deployment_name: Deployment name
            namespace: Kubernetes namespace
            search_term: Term to search for
            tail_lines: Number of lines to search through
            case_sensitive: Case-sensitive search
            
        Returns:
            Dictionary with matching log lines
        """
        try:
            # Get logs from deployment
            logs_result = self.get_deployment_logs(
                deployment_name=deployment_name,
                namespace=namespace,
                tail_lines=tail_lines
            )
            
            if not search_term:
                return logs_result
            
            # Search through logs
            matching_logs = []
            search_term_lower = search_term if case_sensitive else search_term.lower()
            
            for pod_log in logs_result.get("pods", []):
                pod_name = pod_log.get("pod")
                logs = pod_log.get("logs", "")
                
                if not logs:
                    continue
                
                log_lines = logs.split("\n")
                matching_lines = []
                
                for line in log_lines:
                    line_to_search = line if case_sensitive else line.lower()
                    if search_term_lower in line_to_search:
                        matching_lines.append(line)
                
                if matching_lines:
                    matching_logs.append({
                        "pod": pod_name,
                        "matches": len(matching_lines),
                        "logs": "\n".join(matching_lines)
                    })
            
            return {
                "deployment": deployment_name,
                "namespace": namespace,
                "search_term": search_term,
                "pods": matching_logs,
                "total_matches": sum(p.get("matches", 0) for p in matching_logs),
                "retrieved_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to search logs: {e}")
            raise Exception(f"Failed to search logs: {str(e)}")

    def get_logs_since(
        self,
        deployment_name: str,
        namespace: str = "default",
        since_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get logs since a specific time
        
        Args:
            deployment_name: Deployment name
            namespace: Kubernetes namespace
            since_minutes: Minutes ago to retrieve logs from
            
        Returns:
            Dictionary with logs since the specified time
        """
        since_seconds = since_minutes * 60
        
        return self.get_deployment_logs(
            deployment_name=deployment_name,
            namespace=namespace,
            since_seconds=since_seconds,
            tail_lines=10000  # Large number to get all logs since time
        )

    def get_logs_tail(
        self,
        deployment_name: str,
        namespace: str = "default",
        lines: int = 100
    ) -> Dict[str, Any]:
        """
        Get the last N lines of logs (tail)
        
        Args:
            deployment_name: Deployment name
            namespace: Kubernetes namespace
            lines: Number of lines to retrieve
            
        Returns:
            Dictionary with tail of logs
        """
        return self.get_deployment_logs(
            deployment_name=deployment_name,
            namespace=namespace,
            tail_lines=lines
        )

    def aggregate_logs(
        self,
        logs_result: Dict[str, Any],
        sort_by_time: bool = True
    ) -> str:
        """
        Aggregate logs from multiple pods into a single string
        
        Args:
            logs_result: Result from get_deployment_logs or get_service_logs
            sort_by_time: Attempt to sort logs by timestamp (if timestamps are present)
            
        Returns:
            Aggregated log string
        """
        aggregated = []
        pod_logs = logs_result.get("pods", [])
        
        for pod_log in pod_logs:
            pod_name = pod_log.get("pod", "unknown")
            logs = pod_log.get("logs", "")
            
            if logs:
                # Add pod identifier to each line
                log_lines = logs.split("\n")
                for line in log_lines:
                    if line.strip():  # Skip empty lines
                        aggregated.append(f"[{pod_name}] {line}")
        
        if sort_by_time:
            # Simple attempt to sort by timestamp if present
            # In production, you'd use a proper log parser
            try:
                aggregated.sort()
            except Exception:
                pass  # If sorting fails, return unsorted
        
        return "\n".join(aggregated)

    def get_log_statistics(
        self,
        deployment_name: str,
        namespace: str = "default",
        tail_lines: int = 1000
    ) -> Dict[str, Any]:
        """
        Get statistics about logs (error counts, log levels, etc.)
        
        Args:
            deployment_name: Deployment name
            namespace: Kubernetes namespace
            tail_lines: Number of lines to analyze
            
        Returns:
            Dictionary with log statistics
        """
        try:
            logs_result = self.get_deployment_logs(
                deployment_name=deployment_name,
                namespace=namespace,
                tail_lines=tail_lines
            )
            
            stats = {
                "total_pods": logs_result.get("total_pods", 0),
                "total_lines": logs_result.get("total_lines", 0),
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "pod_stats": []
            }
            
            for pod_log in logs_result.get("pods", []):
                pod_name = pod_log.get("pod")
                logs = pod_log.get("logs", "")
                
                if not logs:
                    continue
                
                log_lines = logs.split("\n")
                pod_stat = {
                    "pod": pod_name,
                    "lines": len(log_lines),
                    "errors": 0,
                    "warnings": 0,
                    "info": 0
                }
                
                for line in log_lines:
                    line_lower = line.lower()
                    if "error" in line_lower or "exception" in line_lower or "fatal" in line_lower:
                        pod_stat["errors"] += 1
                        stats["error_count"] += 1
                    elif "warning" in line_lower or "warn" in line_lower:
                        pod_stat["warnings"] += 1
                        stats["warning_count"] += 1
                    elif "info" in line_lower:
                        pod_stat["info"] += 1
                        stats["info_count"] += 1
                
                stats["pod_stats"].append(pod_stat)
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get log statistics: {e}")
            raise Exception(f"Failed to get log statistics: {str(e)}")


# Singleton instance
_logging_service: Optional[LoggingService] = None


def get_logging_service() -> LoggingService:
    """Get or create logging service instance"""
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService()
    return _logging_service

