# Terraform module for provisioning Kubernetes services
# Creates a Deployment and Service for a containerized application

resource "kubernetes_deployment" "service" {
  metadata {
    name      = var.service_name
    namespace = var.namespace
    labels = merge(
      {
        app = var.service_name
        managed-by = "developer-self-service"
      },
      var.labels
    )
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = var.service_name
      }
    }

    template {
      metadata {
        labels = merge(
          {
            app = var.service_name
          },
          var.labels
        )
      }

      spec {
        container {
          name  = var.service_name
          image = var.image

          port {
            container_port = var.container_port
            protocol       = "TCP"
          }

          dynamic "port" {
            for_each = var.additional_ports
            content {
              container_port = port.value
              protocol       = "TCP"
            }
          }

          dynamic "env" {
            for_each = var.env_vars
            content {
              name  = env.key
              value = env.value
            }
          }

          dynamic "env_from" {
            for_each = var.secret_refs
            content {
              secret_ref {
                name = env_from.value
              }
            }
          }

          resources {
            requests = {
              cpu    = var.cpu_request
              memory = var.memory_request
            }
            limits = {
              cpu    = var.cpu_limit
              memory = var.memory_limit
            }
          }

          liveness_probe {
            http_get {
              path = var.health_check_path
              port = var.container_port
            }
            initial_delay_seconds = var.health_check_initial_delay
            period_seconds        = var.health_check_period
            timeout_seconds      = var.health_check_timeout
            failure_threshold     = var.health_check_failure_threshold
          }

          readiness_probe {
            http_get {
              path = var.health_check_path
              port = var.container_port
            }
            initial_delay_seconds = var.readiness_check_initial_delay
            period_seconds        = var.readiness_check_period
            timeout_seconds       = var.readiness_check_timeout
            failure_threshold     = var.readiness_check_failure_threshold
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "service" {
  metadata {
    name      = var.service_name
    namespace = var.namespace
    labels = merge(
      {
        app = var.service_name
        managed-by = "developer-self-service"
      },
      var.labels
    )
  }

  spec {
    type = var.service_type

    selector = {
      app = var.service_name
    }

    port {
      port        = var.service_port
      target_port = var.container_port
      protocol    = "TCP"
    }

    dynamic "port" {
      for_each = var.additional_ports
      content {
        port        = port.value
        target_port = port.value
        protocol    = "TCP"
      }
    }
  }
}

