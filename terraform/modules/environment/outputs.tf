# Output values for the environment module

output "namespace_name" {
  description = "Name of the created namespace"
  value       = kubernetes_namespace.environment.metadata[0].name
}

output "namespace_labels" {
  description = "Labels applied to the namespace"
  value       = kubernetes_namespace.environment.metadata[0].labels
}

output "namespace_annotations" {
  description = "Annotations applied to the namespace"
  value       = kubernetes_namespace.environment.metadata[0].annotations
}

output "environment_id" {
  description = "Environment ID"
  value       = var.environment_id
}

output "environment_name" {
  description = "Environment name"
  value       = var.environment_name
}

output "ttl_hours" {
  description = "Time to live in hours"
  value       = var.ttl_hours
}

output "expires_at" {
  description = "Expiration timestamp"
  value       = var.expires_at
}

output "service_account_name" {
  description = "Name of the service account (if created)"
  value       = var.create_service_account ? kubernetes_service_account.environment[0].metadata[0].name : null
}

output "resource_quota_name" {
  description = "Name of the resource quota (if created)"
  value       = var.create_resource_quota ? kubernetes_resource_quota.environment[0].metadata[0].name : null
}

output "limit_range_name" {
  description = "Name of the limit range (if created)"
  value       = var.create_limit_range ? kubernetes_limit_range.environment[0].metadata[0].name : null
}

