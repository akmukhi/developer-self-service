# Environment Terraform Module

This module provisions a temporary Kubernetes environment by creating a namespace with TTL labels and optional resource management.

## Usage

```hcl
module "temp_environment" {
  source = "./modules/environment"

  namespace_name   = "dev-test-env-abc123"
  environment_id   = "env-abc123"
  environment_name  = "dev-test-env"
  ttl_hours        = 24
  expires_at       = "2024-01-02T00:00:00Z"

  labels = {
    team      = "backend"
    purpose   = "testing"
    project   = "my-project"
  }

  create_resource_quota = true
  create_limit_range    = true
  create_service_account = true
  create_role           = true
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| namespace_name | Name of the Kubernetes namespace | string | - | yes |
| environment_id | Unique identifier for the environment | string | - | yes |
| environment_name | Human-readable name for the environment | string | - | yes |
| ttl_hours | Time to live in hours | number | 24 | no |
| expires_at | ISO timestamp when the environment expires | string | - | yes |
| labels | Additional labels to apply | map(string) | {} | no |
| create_service_account | Create a service account | bool | false | no |
| create_role | Create a role for the service account | bool | false | no |
| create_resource_quota | Create a resource quota | bool | false | no |
| resource_quota_limits | Resource quota limits | map(string) | See defaults | no |
| create_limit_range | Create a limit range | bool | false | no |
| default_cpu_request | Default CPU request | string | "100m" | no |
| default_memory_request | Default memory request | string | "128Mi" | no |
| default_cpu_limit | Default CPU limit | string | "200m" | no |
| default_memory_limit | Default memory limit | string | "256Mi" | no |
| max_cpu_limit | Maximum CPU limit per container | string | "2" | no |
| max_memory_limit | Maximum memory limit per container | string | "4Gi" | no |

## Outputs

| Name | Description |
|------|-------------|
| namespace_name | Name of the created namespace |
| namespace_labels | Labels applied to the namespace |
| namespace_annotations | Annotations applied to the namespace |
| environment_id | Environment ID |
| environment_name | Environment name |
| ttl_hours | Time to live in hours |
| expires_at | Expiration timestamp |
| service_account_name | Name of the service account (if created) |
| resource_quota_name | Name of the resource quota (if created) |
| limit_range_name | Name of the limit range (if created) |

## Features

- Creates a Kubernetes namespace with TTL labels
- Optional service account with RBAC role
- Optional resource quotas to limit namespace resource usage
- Optional limit ranges for default container resource limits
- TTL tracking via labels and annotations
- Custom labels and metadata support

## Resource Quota Example

```hcl
resource_quota_limits = {
  "requests.cpu"    = "4"
  "requests.memory" = "8Gi"
  "limits.cpu"     = "8"
  "limits.memory"  = "16Gi"
  "pods"           = "10"
  "persistentvolumeclaims" = "4"
}
```

## Notes

- The namespace is created with labels indicating it's a temporary environment
- Expiration is tracked via the `expires-at` label and annotation
- Resource quotas help prevent temporary environments from consuming too many cluster resources
- Limit ranges ensure containers have default resource limits even if not specified

