# Terraform module for provisioning temporary Kubernetes environments
# Creates a namespace with TTL labels and optionally deploys services

resource "kubernetes_namespace" "environment" {
  metadata {
    name = var.namespace_name
    labels = merge(
      {
        managed-by           = "developer-self-service"
        environment-id        = var.environment_id
        environment-name      = var.environment_name
        ttl-hours            = tostring(var.ttl_hours)
        expires-at           = var.expires_at
        temporary-environment = "true"
      },
      var.labels
    )
    annotations = {
      "developer-self-service/created-at" = timestamp()
      "developer-self-service/expires-at" = var.expires_at
      "developer-self-service/ttl-hours"  = tostring(var.ttl_hours)
    }
  }
}

# Optional: Create a default service account with limited permissions
resource "kubernetes_service_account" "environment" {
  count = var.create_service_account ? 1 : 0

  metadata {
    name      = "${var.namespace_name}-sa"
    namespace = kubernetes_namespace.environment.metadata[0].name
    labels = merge(
      {
        managed-by = "developer-self-service"
      },
      var.labels
    )
  }
}

# Optional: Create a role for the service account
resource "kubernetes_role" "environment" {
  count = var.create_service_account && var.create_role ? 1 : 0

  metadata {
    name      = "${var.namespace_name}-role"
    namespace = kubernetes_namespace.environment.metadata[0].name
    labels = {
      managed-by = "developer-self-service"
    }
  }

  rule {
    api_groups = [""]
    resources  = ["pods", "services", "configmaps", "secrets"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }

  rule {
    api_groups = ["apps"]
    resources  = ["deployments", "replicasets"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }
}

# Optional: Bind role to service account
resource "kubernetes_role_binding" "environment" {
  count = var.create_service_account && var.create_role ? 1 : 0

  metadata {
    name      = "${var.namespace_name}-rolebinding"
    namespace = kubernetes_namespace.environment.metadata[0].name
    labels = {
      managed-by = "developer-self-service"
    }
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.environment[0].metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.environment[0].metadata[0].name
    namespace = kubernetes_namespace.environment.metadata[0].name
  }
}

# Optional: Create resource quotas to limit resource usage
resource "kubernetes_resource_quota" "environment" {
  count = var.create_resource_quota ? 1 : 0

  metadata {
    name      = "${var.namespace_name}-quota"
    namespace = kubernetes_namespace.environment.metadata[0].name
    labels = {
      managed-by = "developer-self-service"
    }
  }

  spec {
    hard = var.resource_quota_limits
  }
}

# Optional: Create limit range for default resource limits
resource "kubernetes_limit_range" "environment" {
  count = var.create_limit_range ? 1 : 0

  metadata {
    name      = "${var.namespace_name}-limits"
    namespace = kubernetes_namespace.environment.metadata[0].name
    labels = {
      managed-by = "developer-self-service"
    }
  }

  spec {
    limit {
      type = "Container"
      default_request = {
        cpu    = var.default_cpu_request
        memory = var.default_memory_request
      }
      default = {
        cpu    = var.default_cpu_limit
        memory = var.default_memory_limit
      }
      max = {
        cpu    = var.max_cpu_limit
        memory = var.max_memory_limit
      }
    }
  }
}

