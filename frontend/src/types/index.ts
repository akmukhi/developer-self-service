// Type definitions matching backend Pydantic models

// ============================================================================
// Enums (matching backend enums)
// ============================================================================

export enum ServiceStatus {
  PENDING = 'pending',
  CREATING = 'creating',
  RUNNING = 'running',
  FAILED = 'failed',
  STOPPED = 'stopped',
}

export enum DeploymentStatus {
  PENDING = 'pending',
  PROGRESSING = 'progressing',
  AVAILABLE = 'available',
  FAILED = 'failed',
  UNKNOWN = 'unknown',
}

export enum EnvironmentStatus {
  CREATING = 'creating',
  ACTIVE = 'active',
  EXPIRING = 'expiring',
  EXPIRED = 'expired',
  DELETED = 'deleted',
}

export enum SecretType {
  OPAQUE = 'Opaque',
  TLS = 'kubernetes.io/tls',
  DOCKER_CONFIG = 'kubernetes.io/dockerconfigjson',
  BASIC_AUTH = 'kubernetes.io/basic-auth',
  SSH_AUTH = 'kubernetes.io/ssh-auth',
}

// ============================================================================
// Service Types (matching backend/app/models/service.py)
// ============================================================================

export interface ResourceRequirements {
  cpu: string
  memory: string
}

export interface ServiceCreateRequest {
  name: string
  image: string
  replicas?: number
  namespace?: string
  resources?: ResourceRequirements
  env_vars?: Record<string, string>
  ports?: number[]
}

export interface Service {
  id: string
  name: string
  image: string
  replicas: number
  namespace: string
  status: ServiceStatus
  resources: ResourceRequirements
  env_vars: Record<string, string>
  ports: number[]
  created_at: string
  updated_at?: string
  metadata?: Record<string, any>
}

// ============================================================================
// Deployment Types (matching backend/app/models/deployment.py)
// ============================================================================

export interface PodStatus {
  ready: number
  desired: number
  available: number
  unavailable: number
}

export interface Deployment {
  id: string
  service_id: string
  name: string
  namespace: string
  image: string
  image_tag?: string
  status: DeploymentStatus
  replicas: PodStatus
  created_at: string
  updated_at?: string
  metadata?: Record<string, any>
}

// ============================================================================
// Environment Types (matching backend/app/models/environment.py)
// ============================================================================

export interface EnvironmentCreateRequest {
  name: string
  ttl_hours?: number
  namespace?: string
  services?: string[]
  labels?: Record<string, string>
}

export interface Environment {
  id: string
  name: string
  namespace: string
  status: EnvironmentStatus
  ttl_hours: number
  created_at: string
  expires_at: string
  deleted_at?: string
  services: string[]
  labels: Record<string, string>
  metadata?: Record<string, any>
}

// ============================================================================
// Secret Types (matching backend/app/models/secret.py)
// ============================================================================

export interface SecretRotationHistory {
  rotated_at: string
  rotated_by?: string
  version: string
}

export interface SecretRotateRequest {
  keys?: string[]
  generate_new?: boolean
  update_deployments?: boolean
}

export interface Secret {
  id: string
  service_id: string
  name: string
  namespace: string
  secret_type: SecretType
  keys: string[]
  last_rotated?: string
  rotation_history: SecretRotationHistory[]
  created_at: string
  updated_at?: string
  metadata?: Record<string, any>
}

// ============================================================================
// Observability Types (for logs and metrics responses)
// ============================================================================

export interface LogsResponse {
  service_id?: string
  deployment_id?: string
  namespace: string
  deployment: string
  pods: Array<{
    pod: string
    status?: string
    ready?: boolean
    logs: string
    lines: number
    error?: string
    retrieved_at?: string
  }>
  total_pods: number
  total_lines: number
  retrieved_at: string
}

export interface AggregatedLogsResponse {
  service_id: string
  namespace: string
  deployment: string
  aggregated_logs: string
  total_pods: number
  total_lines: number
  retrieved_at: string
}

export interface LogStatistics {
  total_pods: number
  total_lines: number
  error_count: number
  warning_count: number
  info_count: number
  pod_stats: Array<{
    pod: string
    lines: number
    errors: number
    warnings: number
    info: number
  }>
}

export interface PodMetrics {
  pod: string
  status?: string
  cpu: number
  memory: number
  containers?: Array<{
    container: string
    cpu: {
      usage: number
      usage_raw: string
    }
    memory: {
      usage: number
      usage_raw: string
    }
  }>
}

export interface MetricsResponse {
  service_id?: string
  deployment_id?: string
  namespace: string
  deployment?: string
  pods: PodMetrics[]
  aggregated: {
    total_cpu: string
    total_memory: string
    average_cpu?: string
    average_memory?: string
    pod_count: number
  }
  retrieved_at: string
}

export interface MetricsSummary {
  deployment: string
  namespace: string
  summary: {
    pod_count: number
    total_cpu: string
    total_memory: string
    average_cpu: string
    average_memory: string
  }
  pods: Array<{
    pod: string
    cpu: string
    memory: string
  }>
  retrieved_at: string
}

export interface MetricsAvailability {
  available: boolean
  reason: string
  timestamp?: string
}

// ============================================================================
// Health Check Types
// ============================================================================

export interface HealthCheck {
  status: string
}

// ============================================================================
// Utility Types
// ============================================================================

export type StatusType = ServiceStatus | DeploymentStatus | EnvironmentStatus

export interface ApiError {
  detail: string
  status_code?: number
}
