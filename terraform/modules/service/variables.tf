# Input variables for the service module

variable "service_name" {
  description = "Name of the service"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "image" {
  description = "Container image to deploy"
  type        = string
}

variable "replicas" {
  description = "Number of replicas"
  type        = number
  default     = 1
}

variable "container_port" {
  description = "Container port to expose"
  type        = number
  default     = 80
}

variable "service_port" {
  description = "Service port"
  type        = number
  default     = 80
}

variable "additional_ports" {
  description = "Additional container ports to expose"
  type        = list(number)
  default     = []
}

variable "service_type" {
  description = "Kubernetes service type (ClusterIP, NodePort, LoadBalancer)"
  type        = string
  default     = "ClusterIP"
}

variable "env_vars" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

variable "secret_refs" {
  description = "List of secret names to load as environment variables"
  type        = list(string)
  default     = []
}

variable "cpu_request" {
  description = "CPU request (e.g., '100m', '0.5')"
  type        = string
  default     = "100m"
}

variable "memory_request" {
  description = "Memory request (e.g., '128Mi', '1Gi')"
  type        = string
  default     = "128Mi"
}

variable "cpu_limit" {
  description = "CPU limit (e.g., '200m', '1')"
  type        = string
  default     = "200m"
}

variable "memory_limit" {
  description = "Memory limit (e.g., '256Mi', '2Gi')"
  type        = string
  default     = "256Mi"
}

variable "health_check_path" {
  description = "Path for health check endpoint"
  type        = string
  default     = "/health"
}

variable "health_check_initial_delay" {
  description = "Initial delay for liveness probe (seconds)"
  type        = number
  default     = 30
}

variable "health_check_period" {
  description = "Period for liveness probe (seconds)"
  type        = number
  default     = 10
}

variable "health_check_timeout" {
  description = "Timeout for liveness probe (seconds)"
  type        = number
  default     = 5
}

variable "health_check_failure_threshold" {
  description = "Failure threshold for liveness probe"
  type        = number
  default     = 3
}

variable "readiness_check_initial_delay" {
  description = "Initial delay for readiness probe (seconds)"
  type        = number
  default     = 10
}

variable "readiness_check_period" {
  description = "Period for readiness probe (seconds)"
  type        = number
  default     = 10
}

variable "readiness_check_timeout" {
  description = "Timeout for readiness probe (seconds)"
  type        = number
  default     = 5
}

variable "readiness_check_failure_threshold" {
  description = "Failure threshold for readiness probe"
  type        = number
  default     = 3
}

variable "labels" {
  description = "Additional labels to apply to resources"
  type        = map(string)
  default     = {}
}

