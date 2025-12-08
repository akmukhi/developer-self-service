"""
Metrics service
Handles querying Kubernetes metrics API for pod and node metrics
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.services.kubernetes_service import get_kubernetes_service

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for querying Kubernetes metrics"""

    def __init__(self):
        """Initialize metrics service"""
        self.kubernetes = get_kubernetes_service()

    def get_pod_metrics(
        self,
        namespace: str = "default",
        pod_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metrics for pods
        
        Args:
            namespace: Kubernetes namespace
            pod_name: Specific pod name (optional, if None returns all pods)
            
        Returns:
            Dictionary with pod metrics
        """
        try:
            if not self.kubernetes.is_connected:
                raise Exception("Not connected to Kubernetes cluster")
            
            # Check if metrics API is available
            if not self.kubernetes._metrics_v1beta1:
                raise Exception("Metrics API not available. Ensure metrics-server is installed.")
            
            if pod_name:
                # Get specific pod metrics
                try:
                    metrics = self.kubernetes._metrics_v1beta1.read_namespaced_pod_metrics(
                        name=pod_name,
                        namespace=namespace
                    )
                    
                    pod_metrics = []
                    for container in metrics.containers:
                        cpu = self._parse_quantity(container.usage.get("cpu", "0"))
                        memory = self._parse_quantity(container.usage.get("memory", "0"))
                        
                        pod_metrics.append({
                            "container": container.name,
                            "cpu": {
                                "usage": cpu,
                                "usage_raw": container.usage.get("cpu", "0")
                            },
                            "memory": {
                                "usage": memory,
                                "usage_raw": container.usage.get("memory", "0")
                            }
                        })
                    
                    return {
                        "pod": pod_name,
                        "namespace": namespace,
                        "containers": pod_metrics,
                        "timestamp": metrics.timestamp.isoformat() if metrics.timestamp else None,
                        "window": metrics.window.seconds if metrics.window else None
                    }
                except Exception as e:
                    logger.error(f"Failed to get metrics for pod {pod_name}: {e}")
                    raise Exception(f"Failed to get pod metrics: {str(e)}")
            else:
                # Get all pod metrics in namespace
                metrics_list = self.kubernetes.get_pod_metrics(namespace=namespace)
                
                return {
                    "namespace": namespace,
                    "pods": metrics_list,
                    "count": len(metrics_list),
                    "retrieved_at": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to get pod metrics: {e}")
            raise Exception(f"Failed to get pod metrics: {str(e)}")

    def get_deployment_metrics(
        self,
        deployment_name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for a deployment
        
        Args:
            deployment_name: Deployment name
            namespace: Kubernetes namespace
            
        Returns:
            Dictionary with aggregated deployment metrics
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
                logger.warning(f"No pods found for deployment {deployment_name}")
                return {
                    "deployment": deployment_name,
                    "namespace": namespace,
                    "pods": [],
                    "aggregated": {
                        "total_cpu": "0",
                        "total_memory": "0",
                        "average_cpu": "0",
                        "average_memory": "0"
                    },
                    "retrieved_at": datetime.utcnow().isoformat()
                }
            
            # Get metrics for each pod
            pod_metrics_list = []
            total_cpu = 0
            total_memory = 0
            valid_pods = 0
            
            for pod in pods:
                pod_name = pod.get("name")
                if not pod_name:
                    continue
                
                try:
                    pod_metric = self.get_pod_metrics(namespace=namespace, pod_name=pod_name)
                    
                    # Aggregate container metrics
                    pod_cpu = 0
                    pod_memory = 0
                    
                    for container in pod_metric.get("containers", []):
                        cpu_usage = container.get("cpu", {}).get("usage", 0)
                        memory_usage = container.get("memory", {}).get("usage", 0)
                        
                        pod_cpu += cpu_usage
                        pod_memory += memory_usage
                    
                    total_cpu += pod_cpu
                    total_memory += pod_memory
                    valid_pods += 1
                    
                    pod_metrics_list.append({
                        "pod": pod_name,
                        "status": pod.get("status"),
                        "cpu": pod_cpu,
                        "memory": pod_memory,
                        "containers": pod_metric.get("containers", [])
                    })
                except Exception as e:
                    logger.warning(f"Failed to get metrics for pod {pod_name}: {e}")
                    pod_metrics_list.append({
                        "pod": pod_name,
                        "status": pod.get("status"),
                        "error": str(e)
                    })
            
            # Calculate averages
            avg_cpu = total_cpu / valid_pods if valid_pods > 0 else 0
            avg_memory = total_memory / valid_pods if valid_pods > 0 else 0
            
            return {
                "deployment": deployment_name,
                "namespace": namespace,
                "pods": pod_metrics_list,
                "aggregated": {
                    "total_cpu": self._format_quantity(total_cpu, "cpu"),
                    "total_memory": self._format_quantity(total_memory, "memory"),
                    "average_cpu": self._format_quantity(avg_cpu, "cpu"),
                    "average_memory": self._format_quantity(avg_memory, "memory"),
                    "pod_count": valid_pods
                },
                "retrieved_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get deployment metrics: {e}")
            raise Exception(f"Failed to get deployment metrics: {str(e)}")

    def get_service_metrics(
        self,
        service_id: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Get metrics for a service (finds deployment by service ID)
        
        Args:
            service_id: Service identifier
            namespace: Kubernetes namespace
            
        Returns:
            Dictionary with service metrics
        """
        try:
            # Try to find deployment by service ID
            # In a real implementation, you'd have a mapping of service_id to deployment
            try:
                return self.get_deployment_metrics(
                    deployment_name=service_id,
                    namespace=namespace
                )
            except Exception as e:
                logger.warning(f"Failed to get metrics via deployment name: {e}")
            
            # Try to find by label
            pods = self.kubernetes.get_pods(
                namespace=namespace,
                label_selector=f"service={service_id}"
            )
            
            if not pods:
                raise Exception(f"No pods found for service {service_id}")
            
            # Aggregate metrics from all pods
            pod_metrics_list = []
            total_cpu = 0
            total_memory = 0
            valid_pods = 0
            
            for pod in pods:
                pod_name = pod.get("name")
                if not pod_name:
                    continue
                
                try:
                    pod_metric = self.get_pod_metrics(namespace=namespace, pod_name=pod_name)
                    
                    pod_cpu = 0
                    pod_memory = 0
                    
                    for container in pod_metric.get("containers", []):
                        pod_cpu += container.get("cpu", {}).get("usage", 0)
                        pod_memory += container.get("memory", {}).get("usage", 0)
                    
                    total_cpu += pod_cpu
                    total_memory += pod_memory
                    valid_pods += 1
                    
                    pod_metrics_list.append({
                        "pod": pod_name,
                        "cpu": pod_cpu,
                        "memory": pod_memory
                    })
                except Exception as e:
                    logger.warning(f"Failed to get metrics for pod {pod_name}: {e}")
            
            return {
                "service_id": service_id,
                "namespace": namespace,
                "pods": pod_metrics_list,
                "aggregated": {
                    "total_cpu": self._format_quantity(total_cpu, "cpu"),
                    "total_memory": self._format_quantity(total_memory, "memory"),
                    "pod_count": valid_pods
                },
                "retrieved_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")
            raise Exception(f"Failed to get service metrics: {str(e)}")

    def get_node_metrics(self) -> List[Dict[str, Any]]:
        """
        Get metrics for all nodes
        
        Returns:
            List of node metrics
        """
        try:
            if not self.kubernetes.is_connected:
                raise Exception("Not connected to Kubernetes cluster")
            
            if not self.kubernetes._metrics_v1beta1:
                raise Exception("Metrics API not available. Ensure metrics-server is installed.")
            
            metrics_list = self.kubernetes._metrics_v1beta1.list_node_metrics()
            
            node_metrics = []
            for item in metrics_list.items:
                cpu = self._parse_quantity(item.usage.get("cpu", "0"))
                memory = self._parse_quantity(item.usage.get("memory", "0"))
                
                node_metrics.append({
                    "node": item.metadata.name,
                    "cpu": {
                        "usage": cpu,
                        "usage_raw": item.usage.get("cpu", "0")
                    },
                    "memory": {
                        "usage": memory,
                        "usage_raw": item.usage.get("memory", "0")
                    },
                    "timestamp": item.timestamp.isoformat() if item.timestamp else None,
                    "window": item.window.seconds if item.window else None
                })
            
            return node_metrics
        except Exception as e:
            logger.error(f"Failed to get node metrics: {e}")
            raise Exception(f"Failed to get node metrics: {str(e)}")

    def get_namespace_metrics(self, namespace: str = "default") -> Dict[str, Any]:
        """
        Get aggregated metrics for all pods in a namespace
        
        Args:
            namespace: Kubernetes namespace
            
        Returns:
            Dictionary with namespace-level metrics
        """
        try:
            pod_metrics = self.get_pod_metrics(namespace=namespace)
            
            pods = pod_metrics.get("pods", [])
            
            total_cpu = 0
            total_memory = 0
            pod_count = len(pods)
            
            for pod_metric in pods:
                try:
                    cpu_raw = pod_metric.get("cpu", "0")
                    memory_raw = pod_metric.get("memory", "0")
                    
                    total_cpu += self._parse_quantity(cpu_raw)
                    total_memory += self._parse_quantity(memory_raw)
                except Exception as e:
                    logger.warning(f"Failed to parse metrics for pod: {e}")
            
            return {
                "namespace": namespace,
                "pod_count": pod_count,
                "aggregated": {
                    "total_cpu": self._format_quantity(total_cpu, "cpu"),
                    "total_memory": self._format_quantity(total_memory, "memory"),
                    "average_cpu": self._format_quantity(total_cpu / pod_count if pod_count > 0 else 0, "cpu"),
                    "average_memory": self._format_quantity(total_memory / pod_count if pod_count > 0 else 0, "memory")
                },
                "pods": pods,
                "retrieved_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get namespace metrics: {e}")
            raise Exception(f"Failed to get namespace metrics: {str(e)}")

    def _parse_quantity(self, quantity: str) -> float:
        """
        Parse Kubernetes quantity string to numeric value
        
        Args:
            quantity: Kubernetes quantity string (e.g., "100m", "1Gi", "500Mi")
            
        Returns:
            Numeric value in base units
        """
        if not quantity or quantity == "0":
            return 0.0
        
        quantity = quantity.strip()
        
        # CPU: convert to cores (millicores to cores)
        if quantity.endswith("m"):
            try:
                return float(quantity[:-1]) / 1000.0
            except ValueError:
                return 0.0
        elif quantity.endswith("n"):
            try:
                return float(quantity[:-1]) / 1000000000.0  # nanocores to cores
            except ValueError:
                return 0.0
        
        # Memory: convert to bytes
        multipliers = {
            "Ki": 1024,
            "Mi": 1024 ** 2,
            "Gi": 1024 ** 3,
            "Ti": 1024 ** 4,
            "Pi": 1024 ** 5,
            "Ei": 1024 ** 6,
            "K": 1000,
            "M": 1000 ** 2,
            "G": 1000 ** 3,
            "T": 1000 ** 4,
            "P": 1000 ** 5,
            "E": 1000 ** 6,
        }
        
        # Try to find a multiplier
        for suffix, multiplier in multipliers.items():
            if quantity.endswith(suffix):
                try:
                    return float(quantity[:-len(suffix)]) * multiplier
                except ValueError:
                    return 0.0
        
        # Try to parse as plain number (assume bytes for memory, cores for CPU)
        try:
            return float(quantity)
        except ValueError:
            return 0.0

    def _format_quantity(self, value: float, resource_type: str = "memory") -> str:
        """
        Format numeric value to Kubernetes quantity string
        
        Args:
            value: Numeric value
            resource_type: "cpu" or "memory"
            
        Returns:
            Formatted quantity string
        """
        if resource_type == "cpu":
            # Format as cores or millicores
            if value < 1.0:
                return f"{int(value * 1000)}m"
            else:
                return f"{value:.2f}"
        else:
            # Format as memory (bytes to human-readable)
            if value < 1024:
                return f"{int(value)}B"
            elif value < 1024 ** 2:
                return f"{value / 1024:.2f}Ki"
            elif value < 1024 ** 3:
                return f"{value / (1024 ** 2):.2f}Mi"
            elif value < 1024 ** 4:
                return f"{value / (1024 ** 3):.2f}Gi"
            else:
                return f"{value / (1024 ** 4):.2f}Ti"

    def get_metrics_summary(
        self,
        deployment_name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Get a summary of metrics for a deployment
        
        Args:
            deployment_name: Deployment name
            namespace: Kubernetes namespace
            
        Returns:
            Dictionary with metrics summary
        """
        try:
            metrics = self.get_deployment_metrics(
                deployment_name=deployment_name,
                namespace=namespace
            )
            
            aggregated = metrics.get("aggregated", {})
            pods = metrics.get("pods", [])
            
            # Calculate resource utilization if we have requests/limits
            # For MVP, we'll just return the usage metrics
            
            return {
                "deployment": deployment_name,
                "namespace": namespace,
                "summary": {
                    "pod_count": aggregated.get("pod_count", 0),
                    "total_cpu": aggregated.get("total_cpu", "0"),
                    "total_memory": aggregated.get("total_memory", "0"),
                    "average_cpu": aggregated.get("average_cpu", "0"),
                    "average_memory": aggregated.get("average_memory", "0")
                },
                "pods": [
                    {
                        "pod": p.get("pod"),
                        "cpu": self._format_quantity(p.get("cpu", 0), "cpu"),
                        "memory": self._format_quantity(p.get("memory", 0), "memory")
                    }
                    for p in pods if "error" not in p
                ],
                "retrieved_at": metrics.get("retrieved_at")
            }
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            raise Exception(f"Failed to get metrics summary: {str(e)}")

    def check_metrics_available(self) -> Dict[str, Any]:
        """
        Check if metrics API is available
        
        Returns:
            Dictionary with availability status
        """
        try:
            if not self.kubernetes.is_connected:
                return {
                    "available": False,
                    "reason": "Not connected to Kubernetes cluster"
                }
            
            if not self.kubernetes._metrics_v1beta1:
                return {
                    "available": False,
                    "reason": "Metrics API not initialized. Ensure metrics-server is installed."
                }
            
            # Try to query metrics to verify availability
            try:
                self.kubernetes._metrics_v1beta1.list_node_metrics(limit=1)
                return {
                    "available": True,
                    "reason": "Metrics API is available"
                }
            except Exception as e:
                return {
                    "available": False,
                    "reason": f"Metrics API query failed: {str(e)}"
                }
        except Exception as e:
            return {
                "available": False,
                "reason": f"Error checking metrics availability: {str(e)}"
            }


# Singleton instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get or create metrics service instance"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service

