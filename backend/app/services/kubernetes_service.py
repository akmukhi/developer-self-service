"""
Kubernetes API client service
Handles all interactions with the Kubernetes cluster
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

logger = logging.getLogger(__name__)


class KubernetesService:
    """Service for interacting with Kubernetes API"""

    def __init__(self):
        """Initialize Kubernetes client"""
        self._core_v1 = None
        self._apps_v1 = None
        self._metrics_v1beta1 = None
        self._connected = False
        self._connect()

    def _connect(self) -> bool:
        """Connect to Kubernetes cluster"""
        try:
            # Try to load kubeconfig (for local development)
            try:
                config.load_kube_config()
                logger.info("Loaded kubeconfig from default location")
            except config.ConfigException:
                # Try in-cluster config (for when running in Kubernetes)
                try:
                    config.load_incluster_config()
                    logger.info("Loaded in-cluster Kubernetes config")
                except config.ConfigException:
                    logger.error("Could not load Kubernetes config")
                    return False

            # Initialize API clients
            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
            
            # Try to initialize metrics client (may not be available)
            try:
                from kubernetes.client import MetricsV1beta1Api
                self._metrics_v1beta1 = MetricsV1beta1Api()
            except Exception as e:
                logger.warning(f"Metrics API not available: {e}")
                self._metrics_v1beta1 = None

            # Test connection
            self._core_v1.list_namespaces(limit=1)
            self._connected = True
            logger.info("Successfully connected to Kubernetes cluster")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Kubernetes: {e}")
            self._connected = False
            return False

    @property
    def is_connected(self) -> bool:
        """Check if connected to Kubernetes cluster"""
        return self._connected

    def ensure_connected(self):
        """Ensure connection to cluster, reconnect if needed"""
        if not self._connected:
            self._connect()
        if not self._connected:
            raise ConnectionError("Not connected to Kubernetes cluster")

    # Namespace operations
    def create_namespace(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a Kubernetes namespace"""
        self.ensure_connected()
        
        namespace_body = client.V1Namespace(
            metadata=client.V1ObjectMeta(
                name=name,
                labels=labels or {}
            )
        )
        
        try:
            namespace = self._core_v1.create_namespace(body=namespace_body)
            logger.info(f"Created namespace: {name}")
            return {
                "name": namespace.metadata.name,
                "created_at": namespace.metadata.creation_timestamp.isoformat() if namespace.metadata.creation_timestamp else None,
                "labels": namespace.metadata.labels or {}
            }
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.warning(f"Namespace {name} already exists")
                return self.get_namespace(name)
            raise Exception(f"Failed to create namespace: {e.reason}")

    def get_namespace(self, name: str) -> Optional[Dict[str, Any]]:
        """Get namespace information"""
        self.ensure_connected()
        
        try:
            namespace = self._core_v1.read_namespace(name=name)
            return {
                "name": namespace.metadata.name,
                "created_at": namespace.metadata.creation_timestamp.isoformat() if namespace.metadata.creation_timestamp else None,
                "labels": namespace.metadata.labels or {}
            }
        except ApiException as e:
            if e.status == 404:
                return None
            raise Exception(f"Failed to get namespace: {e.reason}")

    def delete_namespace(self, name: str) -> bool:
        """Delete a Kubernetes namespace"""
        self.ensure_connected()
        
        try:
            self._core_v1.delete_namespace(name=name)
            logger.info(f"Deleted namespace: {name}")
            return True
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Namespace {name} not found")
                return False
            raise Exception(f"Failed to delete namespace: {e.reason}")

    # Deployment operations
    def create_deployment(
        self,
        name: str,
        image: str,
        namespace: str = "default",
        replicas: int = 1,
        env_vars: Optional[Dict[str, str]] = None,
        ports: Optional[List[int]] = None,
        resources: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a Kubernetes deployment"""
        self.ensure_connected()

        # Container environment variables
        env = []
        if env_vars:
            env = [client.V1EnvVar(name=k, value=v) for k, v in env_vars.items()]

        # Container ports
        container_ports = []
        if ports:
            container_ports = [client.V1ContainerPort(container_port=p) for p in ports]

        # Resource requirements
        resource_requirements = None
        if resources:
            resource_requirements = client.V1ResourceRequirements(
                requests={
                    "cpu": resources.get("cpu", "100m"),
                    "memory": resources.get("memory", "128Mi")
                },
                limits={
                    "cpu": resources.get("cpu", "200m"),
                    "memory": resources.get("memory", "256Mi")
                }
            )

        # Container spec
        container = client.V1Container(
            name=name,
            image=image,
            env=env,
            ports=container_ports,
            resources=resource_requirements
        )

        # Pod template
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels=labels or {"app": name}),
            spec=client.V1PodSpec(containers=[container])
        )

        # Deployment spec
        spec = client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels=labels or {"app": name}),
            template=template
        )

        # Deployment
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name, labels=labels or {"app": name}),
            spec=spec
        )

        try:
            created_deployment = self._apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deployment
            )
            logger.info(f"Created deployment {name} in namespace {namespace}")
            return self._deployment_to_dict(created_deployment)
        except ApiException as e:
            raise Exception(f"Failed to create deployment: {e.reason}")

    def get_deployment(self, name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get deployment information"""
        self.ensure_connected()
        
        try:
            deployment = self._apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            return self._deployment_to_dict(deployment)
        except ApiException as e:
            if e.status == 404:
                return None
            raise Exception(f"Failed to get deployment: {e.reason}")

    def list_deployments(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all deployments"""
        self.ensure_connected()
        
        try:
            if namespace:
                deployments = self._apps_v1.list_namespaced_deployment(namespace=namespace)
            else:
                deployments = self._apps_v1.list_deployment_for_all_namespaces()
            
            return [self._deployment_to_dict(d) for d in deployments.items]
        except ApiException as e:
            raise Exception(f"Failed to list deployments: {e.reason}")

    def trigger_rolling_update(self, name: str, namespace: str = "default") -> bool:
        """Trigger a rolling update for a deployment by updating restart annotation"""
        self.ensure_connected()
        
        try:
            deployment = self._apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            
            # Update annotation to trigger rolling restart
            if not deployment.spec.template.metadata.annotations:
                deployment.spec.template.metadata.annotations = {}
            
            from datetime import datetime
            deployment.spec.template.metadata.annotations[
                "kubectl.kubernetes.io/restartedAt"
            ] = datetime.utcnow().isoformat()
            
            # Patch the deployment
            self._apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            
            logger.info(f"Triggered rolling update for deployment {name} in namespace {namespace}")
            return True
        except ApiException as e:
            if e.status == 404:
                raise Exception(f"Deployment {name} not found")
            raise Exception(f"Failed to trigger rolling update: {e.reason}")

    def _deployment_to_dict(self, deployment: client.V1Deployment) -> Dict[str, Any]:
        """Convert Kubernetes deployment to dictionary"""
        status = deployment.status
        spec = deployment.spec
        
        # Determine status
        if status.conditions:
            for condition in status.conditions:
                if condition.type == "Available" and condition.status == "True":
                    deployment_status = "available"
                    break
                elif condition.type == "Progressing" and condition.status == "True":
                    deployment_status = "progressing"
                    break
            else:
                deployment_status = "pending"
        else:
            deployment_status = "unknown"

        # Get image
        image = ""
        if spec.template.spec.containers:
            image = spec.template.spec.containers[0].image

        return {
            "id": f"{deployment.metadata.namespace}/{deployment.metadata.name}",
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "image": image,
            "status": deployment_status,
            "replicas": {
                "ready": status.ready_replicas or 0,
                "desired": spec.replicas or 0,
                "available": status.available_replicas or 0,
                "unavailable": status.unavailable_replicas or 0
            },
            "created_at": deployment.metadata.creation_timestamp.isoformat() if deployment.metadata.creation_timestamp else None,
            "labels": deployment.metadata.labels or {}
        }

    # Service operations
    def create_service(
        self,
        name: str,
        namespace: str = "default",
        ports: Optional[List[Dict[str, Any]]] = None,
        selector: Optional[Dict[str, str]] = None,
        service_type: str = "ClusterIP"
    ) -> Dict[str, Any]:
        """Create a Kubernetes service"""
        self.ensure_connected()

        if not ports:
            ports = [{"port": 80, "targetPort": 80}]

        service_ports = [
            client.V1ServicePort(
                port=p.get("port", 80),
                target_port=p.get("targetPort", 80),
                protocol=p.get("protocol", "TCP")
            )
            for p in ports
        ]

        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1ServiceSpec(
                type=service_type,
                ports=service_ports,
                selector=selector or {"app": name}
            )
        )

        try:
            created_service = self._core_v1.create_namespaced_service(
                namespace=namespace,
                body=service
            )
            logger.info(f"Created service {name} in namespace {namespace}")
            return {
                "name": created_service.metadata.name,
                "namespace": created_service.metadata.namespace,
                "type": created_service.spec.type,
                "cluster_ip": created_service.spec.cluster_ip,
                "ports": [{"port": p.port, "target_port": p.target_port} for p in created_service.spec.ports]
            }
        except ApiException as e:
            if e.status == 409:
                logger.warning(f"Service {name} already exists")
                return self.get_service(name, namespace)
            raise Exception(f"Failed to create service: {e.reason}")

    def get_service(self, name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get service information"""
        self.ensure_connected()
        
        try:
            service = self._core_v1.read_namespaced_service(name=name, namespace=namespace)
            return {
                "name": service.metadata.name,
                "namespace": service.metadata.namespace,
                "type": service.spec.type,
                "cluster_ip": service.spec.cluster_ip,
                "ports": [{"port": p.port, "target_port": p.target_port} for p in service.spec.ports]
            }
        except ApiException as e:
            if e.status == 404:
                return None
            raise Exception(f"Failed to get service: {e.reason}")

    # Secret operations
    def create_secret(
        self,
        name: str,
        namespace: str = "default",
        data: Optional[Dict[str, str]] = None,
        secret_type: str = "Opaque"
    ) -> Dict[str, Any]:
        """Create a Kubernetes secret"""
        self.ensure_connected()

        # Encode values to base64
        import base64
        encoded_data = {}
        if data:
            encoded_data = {k: base64.b64encode(v.encode()).decode() for k, v in data.items()}

        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(name=name),
            type=secret_type,
            data=encoded_data
        )

        try:
            created_secret = self._core_v1.create_namespaced_secret(
                namespace=namespace,
                body=secret
            )
            logger.info(f"Created secret {name} in namespace {namespace}")
            return {
                "name": created_secret.metadata.name,
                "namespace": created_secret.metadata.namespace,
                "type": created_secret.type,
                "keys": list(created_secret.data.keys()) if created_secret.data else []
            }
        except ApiException as e:
            if e.status == 409:
                logger.warning(f"Secret {name} already exists")
                return self.get_secret(name, namespace)
            raise Exception(f"Failed to create secret: {e.reason}")

    def get_secret(self, name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get secret information (metadata only, not values)"""
        self.ensure_connected()
        
        try:
            secret = self._core_v1.read_namespaced_secret(name=name, namespace=namespace)
            return {
                "name": secret.metadata.name,
                "namespace": secret.metadata.namespace,
                "type": secret.type,
                "keys": list(secret.data.keys()) if secret.data else [],
                "created_at": secret.metadata.creation_timestamp.isoformat() if secret.metadata.creation_timestamp else None
            }
        except ApiException as e:
            if e.status == 404:
                return None
            raise Exception(f"Failed to get secret: {e.reason}")

    def update_secret(
        self,
        name: str,
        namespace: str = "default",
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Update a Kubernetes secret"""
        self.ensure_connected()

        # Get existing secret
        try:
            secret = self._core_v1.read_namespaced_secret(name=name, namespace=namespace)
        except ApiException as e:
            if e.status == 404:
                raise Exception(f"Secret {name} not found")
            raise Exception(f"Failed to get secret: {e.reason}")

        # Encode new values to base64
        import base64
        if data:
            encoded_data = {k: base64.b64encode(v.encode()).decode() for k, v in data.items()}
            secret.data = encoded_data

        try:
            updated_secret = self._core_v1.replace_namespaced_secret(
                name=name,
                namespace=namespace,
                body=secret
            )
            logger.info(f"Updated secret {name} in namespace {namespace}")
            return {
                "name": updated_secret.metadata.name,
                "namespace": updated_secret.metadata.namespace,
                "type": updated_secret.type,
                "keys": list(updated_secret.data.keys()) if updated_secret.data else []
            }
        except ApiException as e:
            raise Exception(f"Failed to update secret: {e.reason}")

    def list_secrets(self, namespace: str = "default", label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """List secrets in a namespace"""
        self.ensure_connected()
        
        try:
            secrets_list = self._core_v1.list_namespaced_secret(
                namespace=namespace,
                label_selector=label_selector
            )
            
            return [
                {
                    "name": secret.metadata.name,
                    "namespace": secret.metadata.namespace,
                    "type": secret.type,
                    "keys": list(secret.data.keys()) if secret.data else [],
                    "created_at": secret.metadata.creation_timestamp.isoformat() if secret.metadata.creation_timestamp else None
                }
                for secret in secrets_list.items
            ]
        except ApiException as e:
            raise Exception(f"Failed to list secrets: {e.reason}")

    def delete_secret(self, name: str, namespace: str = "default") -> bool:
        """Delete a Kubernetes secret"""
        self.ensure_connected()
        
        try:
            self._core_v1.delete_namespaced_secret(name=name, namespace=namespace)
            logger.info(f"Deleted secret {name} from namespace {namespace}")
            return True
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Secret {name} not found")
                return False
            raise Exception(f"Failed to delete secret: {e.reason}")

    # Pod and log operations
    def get_pods(self, namespace: str = "default", label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pods in a namespace"""
        self.ensure_connected()
        
        try:
            pods = self._core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            return [
                {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "ready": any(
                        cs.ready for cs in pod.status.container_statuses or []
                    ) if pod.status.container_statuses else False,
                    "created_at": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                }
                for pod in pods.items
            ]
        except ApiException as e:
            raise Exception(f"Failed to get pods: {e.reason}")

    def get_pod_logs(
        self,
        pod_name: str,
        namespace: str = "default",
        container: Optional[str] = None,
        tail_lines: Optional[int] = None,
        since_seconds: Optional[int] = None
    ) -> str:
        """Get logs from a pod"""
        self.ensure_connected()
        
        try:
            logs = self._core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
                since_seconds=since_seconds
            )
            return logs
        except ApiException as e:
            if e.status == 404:
                raise Exception(f"Pod {pod_name} not found")
            raise Exception(f"Failed to get logs: {e.reason}")

    def get_deployment_logs(
        self,
        deployment_name: str,
        namespace: str = "default",
        tail_lines: int = 100
    ) -> List[Dict[str, Any]]:
        """Get logs from all pods in a deployment"""
        self.ensure_connected()
        
        # Get pods for the deployment
        pods = self.get_pods(namespace=namespace, label_selector=f"app={deployment_name}")
        
        logs = []
        for pod in pods:
            try:
                pod_logs = self.get_pod_logs(
                    pod_name=pod["name"],
                    namespace=namespace,
                    tail_lines=tail_lines
                )
                logs.append({
                    "pod": pod["name"],
                    "logs": pod_logs
                })
            except Exception as e:
                logger.warning(f"Failed to get logs for pod {pod['name']}: {e}")
                logs.append({
                    "pod": pod["name"],
                    "logs": f"Error: {str(e)}"
                })
        
        return logs

    # Metrics operations
    def get_pod_metrics(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """Get pod metrics (requires metrics-server)"""
        self.ensure_connected()
        
        if not self._metrics_v1beta1:
            raise Exception("Metrics API not available. Ensure metrics-server is installed.")
        
        try:
            metrics = self._metrics_v1beta1.list_namespaced_pod_metrics(namespace=namespace)
            return [
                {
                    "pod": item.metadata.name,
                    "namespace": item.metadata.namespace,
                    "cpu": item.containers[0].usage.get("cpu", "0") if item.containers else "0",
                    "memory": item.containers[0].usage.get("memory", "0") if item.containers else "0"
                }
                for item in metrics.items
            ]
        except ApiException as e:
            raise Exception(f"Failed to get metrics: {e.reason}")


# Singleton instance
_kubernetes_service: Optional[KubernetesService] = None


def get_kubernetes_service() -> KubernetesService:
    """Get or create Kubernetes service instance"""
    global _kubernetes_service
    if _kubernetes_service is None:
        _kubernetes_service = KubernetesService()
    return _kubernetes_service

