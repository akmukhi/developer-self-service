// Type definitions for the application

export interface Service {
  id: string
  name: string
  image: string
  replicas: number
  namespace: string
  status: 'pending' | 'creating' | 'running' | 'failed' | 'stopped'
  resources: {
    cpu: string
    memory: string
  }
  env_vars: Record<string, string>
  ports: number[]
  created_at: string
  updated_at?: string
  metadata?: Record<string, any>
}

export interface Deployment {
  id: string
  service_id: string
  name: string
  namespace: string
  image: string
  image_tag?: string
  status: 'pending' | 'progressing' | 'available' | 'failed' | 'unknown'
  replicas: {
    ready: number
    desired: number
    available: number
    unavailable: number
  }
  created_at: string
  updated_at?: string
  metadata?: Record<string, any>
}

export interface Environment {
  id: string
  name: string
  namespace: string
  status: 'creating' | 'active' | 'expiring' | 'expired' | 'deleted'
  ttl_hours: number
  created_at: string
  expires_at: string
  deleted_at?: string
  services: string[]
  labels: Record<string, string>
  metadata?: Record<string, any>
}

export interface Secret {
  id: string
  service_id: string
  name: string
  namespace: string
  secret_type: string
  keys: string[]
  last_rotated?: string
  rotation_history: Array<{
    rotated_at: string
    rotated_by?: string
    version: string
  }>
  created_at: string
  updated_at?: string
  metadata?: Record<string, any>
}

// Request types
export interface ServiceCreateRequest {
  name: string
  image: string
  replicas?: number
  namespace?: string
  resources?: {
    cpu?: string
    memory?: string
  }
  env_vars?: Record<string, string>
  ports?: number[]
}

export interface EnvironmentCreateRequest {
  name: string
  ttl_hours?: number
  namespace?: string
  services?: string[]
  labels?: Record<string, string>
}

export interface SecretRotateRequest {
  keys?: string[]
  generate_new?: boolean
  update_deployments?: boolean
}

// Response types for observability
export interface LogsResponse {
  service_id: string
  namespace: string
  deployment: string
  pods: Array<{
    pod: string
    status?: string
    ready?: boolean
    logs: string
    lines: number
    error?: string
  }>
  total_pods: number
  total_lines: number
  retrieved_at: string
}

export interface MetricsResponse {
  service_id: string
  namespace: string
  pods: Array<{
    pod: string
    cpu: number
    memory: number
    containers?: Array<{
      container: string
      cpu: { usage: number; usage_raw: string }
      memory: { usage: number; usage_raw: string }
    }>
  }>
  aggregated: {
    total_cpu: string
    total_memory: string
    average_cpu?: string
    average_memory?: string
    pod_count: number
  }
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

