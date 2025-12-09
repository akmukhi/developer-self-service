# Input variables for the secrets module

variable "secret_name" {
  description = "Name of the Kubernetes secret"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "service_id" {
  description = "Service ID associated with this secret"
  type        = string
}

variable "secret_type" {
  description = "Type of Kubernetes secret (Opaque, kubernetes.io/tls, etc.)"
  type        = string
  default     = "Opaque"
}

variable "secret_data" {
  description = "Secret data (values should be base64 encoded or plain strings - Terraform will encode)"
  type        = map(string)
  default     = {}
}

variable "secret_keys" {
  description = "List of secret keys to generate (if secret_data is empty, random values will be generated)"
  type        = list(string)
  default     = []
}

variable "secret_key_length" {
  description = "Length of generated secret keys (if using secret_keys)"
  type        = number
  default     = 32
}

variable "labels" {
  description = "Additional labels to apply to the secret"
  type        = map(string)
  default     = {}
}

variable "prevent_destroy" {
  description = "Prevent accidental deletion of the secret"
  type        = bool
  default     = false
}

variable "create_config_map" {
  description = "Whether to create an associated ConfigMap for non-sensitive data"
  type        = bool
  default     = false
}

variable "config_map_data" {
  description = "Data for the ConfigMap (non-sensitive configuration)"
  type        = map(string)
  default     = {}
}

variable "create_service_account" {
  description = "Whether to create a service account that can use this secret"
  type        = bool
  default     = false
}

