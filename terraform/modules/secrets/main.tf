# Terraform module for managing Kubernetes secrets
# Creates and manages secrets with optional rotation support

resource "kubernetes_secret" "secret" {
  metadata {
    name      = var.secret_name
    namespace = var.namespace
    labels = merge(
      {
        managed-by = "developer-self-service"
        service-id = var.service_id
      },
      var.labels
    )
    annotations = {
      "developer-self-service/created-at" = timestamp()
      "developer-self-service/service-id" = var.service_id
    }
  }

  type = var.secret_type

  data = local.generated_secret_data

  # Use lifecycle to prevent accidental deletion
  lifecycle {
    prevent_destroy = var.prevent_destroy
  }
}

# Optional: Create a ConfigMap for non-sensitive configuration
resource "kubernetes_config_map" "config" {
  count = var.create_config_map ? 1 : 0

  metadata {
    name      = "${var.secret_name}-config"
    namespace = var.namespace
    labels = merge(
      {
        managed-by = "developer-self-service"
        service-id = var.service_id
      },
      var.labels
    )
  }

  data = var.config_map_data
}

# Optional: Create a service account that can use this secret
resource "kubernetes_service_account" "secret_user" {
  count = var.create_service_account ? 1 : 0

  metadata {
    name      = "${var.secret_name}-sa"
    namespace = var.namespace
    labels = merge(
      {
        managed-by = "developer-self-service"
      },
      var.labels
    )
  }

  secret {
    name = kubernetes_secret.secret.metadata[0].name
  }
}

