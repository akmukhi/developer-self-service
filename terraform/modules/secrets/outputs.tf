# Output values for the secrets module

output "secret_name" {
  description = "Name of the Kubernetes secret"
  value       = kubernetes_secret.secret.metadata[0].name
}

output "secret_namespace" {
  description = "Namespace of the Kubernetes secret"
  value       = kubernetes_secret.secret.metadata[0].namespace
}

output "secret_type" {
  description = "Type of the Kubernetes secret"
  value       = kubernetes_secret.secret.type
}

output "secret_keys" {
  description = "List of keys in the secret (not values)"
  value       = keys(kubernetes_secret.secret.data)
  sensitive   = false
}

output "service_id" {
  description = "Service ID associated with this secret"
  value       = var.service_id
}

output "config_map_name" {
  description = "Name of the ConfigMap (if created)"
  value       = var.create_config_map ? kubernetes_config_map.config[0].metadata[0].name : null
}

output "service_account_name" {
  description = "Name of the service account (if created)"
  value       = var.create_service_account ? kubernetes_service_account.secret_user[0].metadata[0].name : null
}

