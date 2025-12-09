# Output values for the service module

output "deployment_name" {
  description = "Name of the Kubernetes deployment"
  value       = kubernetes_deployment.service.metadata[0].name
}

output "deployment_namespace" {
  description = "Namespace of the Kubernetes deployment"
  value       = kubernetes_deployment.service.metadata[0].namespace
}

output "service_name" {
  description = "Name of the Kubernetes service"
  value       = kubernetes_service.service.metadata[0].name
}

output "service_namespace" {
  description = "Namespace of the Kubernetes service"
  value       = kubernetes_service.service.metadata[0].namespace
}

output "service_cluster_ip" {
  description = "Cluster IP of the Kubernetes service"
  value       = kubernetes_service.service.spec[0].cluster_ip
}

output "service_type" {
  description = "Type of the Kubernetes service"
  value       = kubernetes_service.service.spec[0].type[0]
}

output "selector" {
  description = "Selector labels for the service"
  value       = kubernetes_service.service.spec[0].selector
}

output "replicas" {
  description = "Number of replicas configured"
  value       = kubernetes_deployment.service.spec[0].replicas
}

output "image" {
  description = "Container image used"
  value       = var.image
}

