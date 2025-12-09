# Service Terraform Module

This module provisions a Kubernetes service by creating a Deployment and Service resource.

## Usage

```hcl
module "my_service" {
  source = "./modules/service"

  service_name = "my-service"
  namespace    = "default"
  image        = "nginx:latest"
  replicas     = 2

  container_port = 80
  service_port   = 80

  cpu_request    = "100m"
  memory_request = "128Mi"
  cpu_limit      = "200m"
  memory_limit   = "256Mi"

  env_vars = {
    ENV = "production"
  }

  secret_refs = ["my-service-secrets"]

  labels = {
    team = "backend"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| service_name | Name of the service | string | - | yes |
| namespace | Kubernetes namespace | string | "default" | no |
| image | Container image to deploy | string | - | yes |
| replicas | Number of replicas | number | 1 | no |
| container_port | Container port to expose | number | 80 | no |
| service_port | Service port | number | 80 | no |
| additional_ports | Additional container ports | list(number) | [] | no |
| service_type | Kubernetes service type | string | "ClusterIP" | no |
| env_vars | Environment variables | map(string) | {} | no |
| secret_refs | Secret names to load as env vars | list(string) | [] | no |
| cpu_request | CPU request | string | "100m" | no |
| memory_request | Memory request | string | "128Mi" | no |
| cpu_limit | CPU limit | string | "200m" | no |
| memory_limit | Memory limit | string | "256Mi" | no |
| health_check_path | Health check endpoint path | string | "/health" | no |
| labels | Additional labels | map(string) | {} | no |

## Outputs

| Name | Description |
|------|-------------|
| deployment_name | Name of the Kubernetes deployment |
| deployment_namespace | Namespace of the deployment |
| service_name | Name of the Kubernetes service |
| service_namespace | Namespace of the service |
| service_cluster_ip | Cluster IP of the service |
| service_type | Type of the service |
| selector | Selector labels |
| replicas | Number of replicas |
| image | Container image used |

## Features

- Creates Kubernetes Deployment with configurable replicas
- Creates Kubernetes Service for networking
- Supports environment variables and secret references
- Configurable resource requests and limits
- Health check probes (liveness and readiness)
- Support for multiple ports
- Customizable labels and metadata

