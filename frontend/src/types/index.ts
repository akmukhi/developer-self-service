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

