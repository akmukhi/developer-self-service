# Input variables for the environment module

variable "namespace_name" {
  description = "Name of the Kubernetes namespace"
  type        = string
}

variable "environment_id" {
  description = "Unique identifier for the environment"
  type        = string
}

variable "environment_name" {
  description = "Human-readable name for the environment"
  type        = string
}

variable "ttl_hours" {
  description = "Time to live in hours"
  type        = number
  default     = 24
}

variable "expires_at" {
  description = "ISO timestamp when the environment expires"
  type        = string
}

variable "labels" {
  description = "Additional labels to apply to the namespace"
  type        = map(string)
  default     = {}
}

variable "create_service_account" {
  description = "Whether to create a service account for the environment"
  type        = bool
  default     = false
}

variable "create_role" {
  description = "Whether to create a role for the service account"
  type        = bool
  default     = false
}

variable "create_resource_quota" {
  description = "Whether to create a resource quota for the namespace"
  type        = bool
  default     = false
}

variable "resource_quota_limits" {
  description = "Resource quota limits (e.g., {'requests.cpu': '4', 'requests.memory': '8Gi'})"
  type        = map(string)
  default = {
    "requests.cpu"    = "4"
    "requests.memory" = "8Gi"
    "limits.cpu"     = "8"
    "limits.memory"  = "16Gi"
    "pods"           = "10"
  }
}

variable "create_limit_range" {
  description = "Whether to create a limit range for default resource limits"
  type        = bool
  default     = false
}

variable "default_cpu_request" {
  description = "Default CPU request for containers"
  type        = string
  default     = "100m"
}

variable "default_memory_request" {
  description = "Default memory request for containers"
  type        = string
  default     = "128Mi"
}

variable "default_cpu_limit" {
  description = "Default CPU limit for containers"
  type        = string
  default     = "200m"
}

variable "default_memory_limit" {
  description = "Default memory limit for containers"
  type        = string
  default     = "256Mi"
}

variable "max_cpu_limit" {
  description = "Maximum CPU limit per container"
  type        = string
  default     = "2"
}

variable "max_memory_limit" {
  description = "Maximum memory limit per container"
  type        = string
  default     = "4Gi"
}

