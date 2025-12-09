# Secrets Terraform Module

This module manages Kubernetes secrets with optional automatic generation and associated resources.

## Usage

### Basic Usage with Generated Secrets

```hcl
module "service_secrets" {
  source = "./modules/secrets"

  secret_name = "my-service-secrets"
  namespace   = "default"
  service_id  = "default/my-service"
  
  secret_keys = ["database_url", "api_key", "secret_key"]
  secret_key_length = 32
}
```

### Usage with Provided Secret Data

```hcl
module "service_secrets" {
  source = "./modules/secrets"

  secret_name = "my-service-secrets"
  namespace   = "default"
  service_id  = "default/my-service"
  
  secret_data = {
    database_url = base64encode("postgresql://user:pass@host:5432/db")
    api_key      = base64encode("my-api-key-123")
  }
}
```

### Usage with ConfigMap and Service Account

```hcl
module "service_secrets" {
  source = "./modules/secrets"

  secret_name = "my-service-secrets"
  namespace   = "default"
  service_id  = "default/my-service"
  
  secret_keys = ["database_password", "api_key"]
  
  create_config_map = true
  config_map_data = {
    log_level = "info"
    env       = "production"
  }
  
  create_service_account = true
  prevent_destroy       = true
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| secret_name | Name of the Kubernetes secret | string | - | yes |
| namespace | Kubernetes namespace | string | "default" | no |
| service_id | Service ID associated with this secret | string | - | yes |
| secret_type | Type of Kubernetes secret | string | "Opaque" | no |
| secret_data | Secret data (base64 encoded or plain) | map(string) | {} | no |
| secret_keys | List of keys to generate (if secret_data empty) | list(string) | [] | no |
| secret_key_length | Length of generated secret keys | number | 32 | no |
| labels | Additional labels | map(string) | {} | no |
| prevent_destroy | Prevent accidental deletion | bool | false | no |
| create_config_map | Create associated ConfigMap | bool | false | no |
| config_map_data | ConfigMap data | map(string) | {} | no |
| create_service_account | Create service account | bool | false | no |

## Outputs

| Name | Description |
|------|-------------|
| secret_name | Name of the Kubernetes secret |
| secret_namespace | Namespace of the secret |
| secret_type | Type of the secret |
| secret_keys | List of keys in the secret (not values) |
| service_id | Service ID associated with this secret |
| config_map_name | Name of the ConfigMap (if created) |
| service_account_name | Name of the service account (if created) |

## Features

- Creates Kubernetes secrets with proper labels and annotations
- Automatic secret generation using random_password resource
- Optional ConfigMap for non-sensitive configuration
- Optional service account creation
- Lifecycle protection to prevent accidental deletion
- Support for different secret types (Opaque, TLS, etc.)
- Base64 encoding handled automatically by Terraform

## Secret Types

Supported secret types:
- `Opaque` - Generic secret (default)
- `kubernetes.io/tls` - TLS certificate
- `kubernetes.io/dockerconfigjson` - Docker registry credentials
- `kubernetes.io/basic-auth` - Basic authentication
- `kubernetes.io/ssh-auth` - SSH authentication

## Security Notes

- Secret values are never exposed in outputs (only keys are shown)
- Use `prevent_destroy = true` for production secrets
- Generated secrets use cryptographically secure random generation
- Secrets are base64 encoded automatically by Terraform
- Consider using external secret management (Vault, AWS Secrets Manager) for production

## Example: TLS Secret

```hcl
module "tls_secret" {
  source = "./modules/secrets"

  secret_name = "my-service-tls"
  namespace   = "default"
  service_id  = "default/my-service"
  secret_type = "kubernetes.io/tls"
  
  secret_data = {
    tls.crt = filebase64("cert.crt")
    tls.key = filebase64("cert.key")
  }
  
  prevent_destroy = true
}
```

