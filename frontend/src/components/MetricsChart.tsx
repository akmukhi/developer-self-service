import { useState, useEffect } from 'react'
import {
  Paper,
  Typography,
  Box,
  Button,
  Grid,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material'
import { Refresh, TrendingUp, Memory, Speed } from '@mui/icons-material'
import { api } from '../services/api'
import type { MetricsResponse, MetricsSummary } from '../types'

interface MetricsChartProps {
  serviceId: string
  namespace?: string
  onServiceChange?: (serviceId: string) => void
}

const MetricsChart = ({ serviceId, namespace, onServiceChange }: MetricsChartProps) => {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [summary, setSummary] = useState<MetricsSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'summary' | 'detailed'>('summary')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [autoRefreshInterval, setAutoRefreshInterval] = useState(30) // seconds

  const fetchMetrics = async () => {
    if (!serviceId) return

    try {
      setLoading(true)
      setError(null)

      if (viewMode === 'summary') {
        const data = await api.observability.getMetricsSummary(serviceId, namespace)
        setSummary(data)
      } else {
        const data = await api.observability.getMetrics(serviceId, namespace)
        setMetrics(data)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
      console.error('Error fetching metrics:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMetrics()
  }, [serviceId, namespace, viewMode])

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchMetrics()
      }, autoRefreshInterval * 1000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, autoRefreshInterval, serviceId, namespace, viewMode])

  const parseQuantity = (quantity: string): number => {
    if (!quantity) return 0
    
    // Handle CPU (millicores)
    if (quantity.endsWith('m')) {
      return parseFloat(quantity.slice(0, -1)) / 1000
    }
    
    // Handle memory (Ki, Mi, Gi, etc.)
    const memoryMultipliers: Record<string, number> = {
      Ki: 1024,
      Mi: 1024 ** 2,
      Gi: 1024 ** 3,
      Ti: 1024 ** 4,
    }
    
    for (const [suffix, multiplier] of Object.entries(memoryMultipliers)) {
      if (quantity.endsWith(suffix)) {
        return parseFloat(quantity.slice(0, -suffix.length)) * multiplier
      }
    }
    
    return parseFloat(quantity) || 0
  }

  const formatQuantity = (value: number, type: 'cpu' | 'memory'): string => {
    if (type === 'cpu') {
      if (value < 1) {
        return `${Math.round(value * 1000)}m`
      }
      return value.toFixed(2)
    } else {
      // Memory in bytes
      if (value < 1024) {
        return `${Math.round(value)}B`
      } else if (value < 1024 ** 2) {
        return `${(value / 1024).toFixed(2)}Ki`
      } else if (value < 1024 ** 3) {
        return `${(value / (1024 ** 2)).toFixed(2)}Mi`
      } else {
        return `${(value / (1024 ** 3)).toFixed(2)}Gi`
      }
    }
  }

  return (
    <Paper sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Metrics
        </Typography>
        <Box display="flex" gap={1}>
          <Chip
            label={`Auto: ${autoRefreshInterval}s`}
            color={autoRefresh ? 'primary' : 'default'}
            onClick={() => setAutoRefresh(!autoRefresh)}
            size="small"
          />
          <Button
            size="small"
            startIcon={<Refresh />}
            onClick={fetchMetrics}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* View Mode Toggle */}
      <Box mb={2}>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>View Mode</InputLabel>
          <Select
            value={viewMode}
            label="View Mode"
            onChange={(e) => setViewMode(e.target.value as 'summary' | 'detailed')}
          >
            <MenuItem value="summary">Summary</MenuItem>
            <MenuItem value="detailed">Detailed</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && !metrics && !summary ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress />
        </Box>
      ) : viewMode === 'summary' && summary ? (
        <>
          {/* Summary Cards */}
          <Grid container spacing={2} mb={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <TrendingUp color="primary" />
                    <Typography variant="body2" color="text.secondary">
                      Pod Count
                    </Typography>
                  </Box>
                  <Typography variant="h4">{summary.summary.pod_count}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <Speed color="primary" />
                    <Typography variant="body2" color="text.secondary">
                      Total CPU
                    </Typography>
                  </Box>
                  <Typography variant="h4">{summary.summary.total_cpu}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <Memory color="primary" />
                    <Typography variant="body2" color="text.secondary">
                      Total Memory
                    </Typography>
                  </Box>
                  <Typography variant="h4">{summary.summary.total_memory}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <TrendingUp color="primary" />
                    <Typography variant="body2" color="text.secondary">
                      Avg CPU
                    </Typography>
                  </Box>
                  <Typography variant="h4">{summary.summary.average_cpu}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Pod Metrics Table */}
          {summary.pods.length > 0 && (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Pod</TableCell>
                    <TableCell align="right">CPU</TableCell>
                    <TableCell align="right">Memory</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {summary.pods.map((pod) => (
                    <TableRow key={pod.pod}>
                      <TableCell>{pod.pod}</TableCell>
                      <TableCell align="right">{pod.cpu}</TableCell>
                      <TableCell align="right">{pod.memory}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </>
      ) : metrics ? (
        <>
          {/* Aggregated Metrics */}
          <Grid container spacing={2} mb={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <TrendingUp color="primary" />
                    <Typography variant="body2" color="text.secondary">
                      Total CPU
                    </Typography>
                  </Box>
                  <Typography variant="h4">{metrics.aggregated.total_cpu}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <Memory color="primary" />
                    <Typography variant="body2" color="text.secondary">
                      Total Memory
                    </Typography>
                  </Box>
                  <Typography variant="h4">{metrics.aggregated.total_memory}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <TrendingUp color="primary" />
                    <Typography variant="body2" color="text.secondary">
                      Avg CPU
                    </Typography>
                  </Box>
                  <Typography variant="h4">
                    {metrics.aggregated.average_cpu || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <Memory color="primary" />
                    <Typography variant="body2" color="text.secondary">
                      Avg Memory
                    </Typography>
                  </Box>
                  <Typography variant="h4">
                    {metrics.aggregated.average_memory || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Pod Metrics Table */}
          {metrics.pods.length > 0 && (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Pod</TableCell>
                    <TableCell align="right">CPU Usage</TableCell>
                    <TableCell align="right">Memory Usage</TableCell>
                    <TableCell align="right">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {metrics.pods.map((pod) => {
                    const cpuValue = typeof pod.cpu === 'number' ? pod.cpu : parseQuantity(String(pod.cpu))
                    const memoryValue = typeof pod.memory === 'number' ? pod.memory : parseQuantity(String(pod.memory))
                    
                    return (
                      <TableRow key={pod.pod}>
                        <TableCell>{pod.pod}</TableCell>
                        <TableCell align="right">
                          <Box display="flex" alignItems="center" gap={1} justifyContent="flex-end">
                            <Typography variant="body2">
                              {formatQuantity(cpuValue, 'cpu')}
                            </Typography>
                            {pod.containers && pod.containers.length > 0 && (
                              <Chip
                                label={`${pod.containers.length} container(s)`}
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          {formatQuantity(memoryValue, 'memory')}
                        </TableCell>
                        <TableCell align="right">
                          {pod.status && (
                            <Chip
                              label={pod.status}
                              size="small"
                              color={pod.status === 'Running' ? 'success' : 'default'}
                            />
                          )}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Container Details */}
          {metrics.pods.some((p) => p.containers && p.containers.length > 0) && (
            <Box mt={3}>
              <Typography variant="subtitle2" gutterBottom>
                Container Details
              </Typography>
              {metrics.pods.map((pod) =>
                pod.containers?.map((container) => (
                  <Card key={`${pod.pod}-${container.container}`} sx={{ mb: 1 }}>
                    <CardContent>
                      <Typography variant="body2" fontWeight="medium" gutterBottom>
                        {pod.pod} / {container.container}
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            CPU: {container.cpu.usage_raw}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Memory: {container.memory.usage_raw}
                          </Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                ))
              )}
            </Box>
          )}
        </>
      ) : (
        <Typography color="text.secondary" textAlign="center" sx={{ py: 4 }}>
          No metrics available. Select a service to view metrics.
        </Typography>
      )}

      {/* Timestamp */}
      {metrics && (
        <Box mt={2}>
          <Typography variant="caption" color="text.secondary">
            Retrieved: {new Date(metrics.retrieved_at).toLocaleString()}
          </Typography>
        </Box>
      )}
    </Paper>
  )
}

export default MetricsChart

