import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  Service,
  ServiceCreateRequest,
  Deployment,
  Environment,
  EnvironmentCreateRequest,
  Secret,
  SecretRotateRequest,
  LogsResponse,
  MetricsResponse,
  LogStatistics,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      // Request made but no response received
      console.error('Network Error:', error.request)
    } else {
      // Something else happened
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

// Services API
export const servicesApi = {
  /**
   * Create a new service
   */
  create: async (data: ServiceCreateRequest): Promise<Service> => {
    const response = await apiClient.post<Service>('/services', data)
    return response.data
  },

  /**
   * List all services
   */
  list: async (namespace?: string): Promise<Service[]> => {
    const params = namespace ? { namespace } : {}
    const response = await apiClient.get<Service[]>('/services', { params })
    return response.data
  },

  /**
   * Get service details by ID
   */
  get: async (serviceId: string): Promise<Service> => {
    const response = await apiClient.get<Service>(`/services/${serviceId}`)
    return response.data
  },
}

// Deployments API
export const deploymentsApi = {
  /**
   * List all deployments
   */
  list: async (namespace?: string, serviceId?: string): Promise<Deployment[]> => {
    const params: Record<string, string> = {}
    if (namespace) params.namespace = namespace
    if (serviceId) params.service_id = serviceId
    
    const response = await apiClient.get<Deployment[]>('/deployments', { params })
    return response.data
  },

  /**
   * Get deployment details by ID
   */
  get: async (deploymentId: string): Promise<Deployment> => {
    const response = await apiClient.get<Deployment>(`/deployments/${deploymentId}`)
    return response.data
  },
}

// Environments API
export const environmentsApi = {
  /**
   * Create a temporary environment
   */
  create: async (data: EnvironmentCreateRequest): Promise<Environment> => {
    const response = await apiClient.post<Environment>('/environments', data)
    return response.data
  },

  /**
   * List all environments
   */
  list: async (namespace?: string, statusFilter?: string): Promise<Environment[]> => {
    const params: Record<string, string> = {}
    if (namespace) params.namespace = namespace
    if (statusFilter) params.status_filter = statusFilter
    
    const response = await apiClient.get<Environment[]>('/environments', { params })
    return response.data
  },

  /**
   * Get environment details by ID
   */
  get: async (environmentId: string): Promise<Environment> => {
    const response = await apiClient.get<Environment>(`/environments/${environmentId}`)
    return response.data
  },

  /**
   * Delete/cleanup an environment
   */
  delete: async (environmentId: string): Promise<void> => {
    await apiClient.delete(`/environments/${environmentId}`)
  },
}

// Secrets API
export const secretsApi = {
  /**
   * Rotate secrets for a service
   */
  rotate: async (
    serviceId: string,
    data?: SecretRotateRequest
  ): Promise<Secret> => {
    const response = await apiClient.post<Secret>(
      `/secrets/${serviceId}/rotate`,
      data || {}
    )
    return response.data
  },

  /**
   * Get secret information for a service
   */
  get: async (serviceId: string): Promise<Secret> => {
    const response = await apiClient.get<Secret>(`/secrets/${serviceId}`)
    return response.data
  },

  /**
   * List all secrets
   */
  list: async (namespace?: string, serviceId?: string): Promise<Secret[]> => {
    const params: Record<string, string> = {}
    if (namespace) params.namespace = namespace
    if (serviceId) params.service_id = serviceId
    
    const response = await apiClient.get<Secret[]>('/secrets', { params })
    return response.data
  },

  /**
   * Get rotation history for a service
   */
  getRotationHistory: async (serviceId: string): Promise<Secret['rotation_history']> => {
    const response = await apiClient.get<Secret['rotation_history']>(
      `/secrets/${serviceId}/history`
    )
    return response.data
  },
}

// Observability API
export const observabilityApi = {
  /**
   * Get logs for a service
   */
  getLogs: async (
    serviceId: string,
    options?: {
      lines?: number
      sinceMinutes?: number
      search?: string
      namespace?: string
    }
  ): Promise<LogsResponse> => {
    const params: Record<string, string | number> = {}
    if (options?.lines) params.lines = options.lines
    if (options?.sinceMinutes) params.since_minutes = options.sinceMinutes
    if (options?.search) params.search = options.search
    if (options?.namespace) params.namespace = options.namespace
    
    const response = await apiClient.get<LogsResponse>(`/logs/${serviceId}`, { params })
    return response.data
  },

  /**
   * Get aggregated logs for a service
   */
  getAggregatedLogs: async (
    serviceId: string,
    lines?: number,
    namespace?: string
  ): Promise<{ aggregated_logs: string; total_pods: number; total_lines: number }> => {
    const params: Record<string, string | number> = {}
    if (lines) params.lines = lines
    if (namespace) params.namespace = namespace
    
    const response = await apiClient.get(`/logs/${serviceId}/aggregated`, { params })
    return response.data
  },

  /**
   * Get log statistics for a service
   */
  getLogStatistics: async (
    serviceId: string,
    lines?: number,
    namespace?: string
  ): Promise<LogStatistics> => {
    const params: Record<string, string | number> = {}
    if (lines) params.lines = lines
    if (namespace) params.namespace = namespace
    
    const response = await apiClient.get<LogStatistics>(
      `/logs/${serviceId}/statistics`,
      { params }
    )
    return response.data
  },

  /**
   * Get metrics for a service
   */
  getMetrics: async (serviceId: string, namespace?: string): Promise<MetricsResponse> => {
    const params: Record<string, string> = {}
    if (namespace) params.namespace = namespace
    
    const response = await apiClient.get<MetricsResponse>(`/metrics/${serviceId}`, {
      params,
    })
    return response.data
  },

  /**
   * Get metrics summary for a service
   */
  getMetricsSummary: async (
    serviceId: string,
    namespace?: string
  ): Promise<MetricsResponse['aggregated'] & { pods: Array<{ pod: string; cpu: string; memory: string }> }> => {
    const params: Record<string, string> = {}
    if (namespace) params.namespace = namespace
    
    const response = await apiClient.get(`/metrics/${serviceId}/summary`, { params })
    return response.data
  },

  /**
   * Check metrics API availability
   */
  checkMetricsAvailability: async (): Promise<{
    available: boolean
    reason: string
  }> => {
    const response = await apiClient.get('/metrics/availability')
    return response.data
  },

  /**
   * Get logs for a deployment
   */
  getDeploymentLogs: async (
    deploymentId: string,
    options?: {
      lines?: number
      sinceMinutes?: number
      search?: string
      namespace?: string
    }
  ): Promise<LogsResponse> => {
    const params: Record<string, string | number> = {}
    if (options?.lines) params.lines = options.lines
    if (options?.sinceMinutes) params.since_minutes = options.sinceMinutes
    if (options?.search) params.search = options.search
    if (options?.namespace) params.namespace = options.namespace
    
    const response = await apiClient.get<LogsResponse>(
      `/deployments/${deploymentId}/logs`,
      { params }
    )
    return response.data
  },

  /**
   * Get metrics for a deployment
   */
  getDeploymentMetrics: async (
    deploymentId: string,
    namespace?: string
  ): Promise<MetricsResponse> => {
    const params: Record<string, string> = {}
    if (namespace) params.namespace = namespace
    
    const response = await apiClient.get<MetricsResponse>(
      `/deployments/${deploymentId}/metrics`,
      { params }
    )
    return response.data
  },
}

// Health check
export const healthApi = {
  /**
   * Check API health
   */
  check: async (): Promise<{ status: string }> => {
    const response = await apiClient.get<{ status: string }>('/health')
    return response.data
  },
}

// Export default client for custom requests
export default apiClient

// Export all APIs as a single object for convenience
export const api = {
  services: servicesApi,
  deployments: deploymentsApi,
  environments: environmentsApi,
  secrets: secretsApi,
  observability: observabilityApi,
  health: healthApi,
}
