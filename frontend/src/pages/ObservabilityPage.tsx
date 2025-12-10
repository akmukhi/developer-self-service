import { useState, useEffect } from 'react'
import {
  Typography,
  Box,
  Grid,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  TextField,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
} from '@mui/material'
import { Assessment, BarChart, List } from '@mui/icons-material'
import LogViewer from '../components/LogViewer'
import MetricsChart from '../components/MetricsChart'
import { api } from '../services/api'
import type { Service } from '../types'

const ObservabilityPage = () => {
  const [services, setServices] = useState<Service[]>([])
  const [selectedService, setSelectedService] = useState<string>('')
  const [selectedNamespace, setSelectedNamespace] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tabValue, setTabValue] = useState(0)
  const [metricsAvailable, setMetricsAvailable] = useState<boolean | null>(null)

  const fetchServices = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.services.list()
      setServices(data)
      
      // Auto-select first service if available
      if (data.length > 0 && !selectedService) {
        setSelectedService(data[0].id)
        setSelectedNamespace(data[0].namespace)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch services')
      console.error('Error fetching services:', err)
    } finally {
      setLoading(false)
    }
  }

  const checkMetricsAvailability = async () => {
    try {
      const availability = await api.observability.checkMetricsAvailability()
      setMetricsAvailable(availability.available)
    } catch (err) {
      setMetricsAvailable(false)
    }
  }

  useEffect(() => {
    fetchServices()
    checkMetricsAvailability()
  }, [])

  const handleServiceChange = (serviceId: string) => {
    setSelectedService(serviceId)
    const service = services.find((s) => s.id === serviceId)
    if (service) {
      setSelectedNamespace(service.namespace)
    }
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const serviceOptions = services.map((service) => ({
    label: `${service.name} (${service.namespace})`,
    value: service.id,
  }))

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
            Observability
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            View logs and metrics for your services
          </Typography>
        </Box>
      </Box>

      {/* Service Selection */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Autocomplete
              options={serviceOptions}
              value={serviceOptions.find((opt) => opt.value === selectedService) || null}
              onChange={(_event, newValue) => {
                if (newValue) {
                  handleServiceChange(newValue.value)
                }
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Select Service"
                  placeholder="Choose a service to view logs and metrics"
                />
              )}
              loading={loading}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Namespace (Optional Override)"
              value={selectedNamespace}
              onChange={(e) => setSelectedNamespace(e.target.value)}
              placeholder="Leave empty to use service namespace"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Metrics Availability Warning */}
      {metricsAvailable === false && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Metrics API is not available. Ensure metrics-server is installed in your Kubernetes cluster.
          Logs will still be available.
        </Alert>
      )}

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && services.length === 0 ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : !selectedService ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Service Selected
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Select a service from the dropdown above to view logs and metrics
          </Typography>
        </Paper>
      ) : (
        <>
          {/* Tabs */}
          <Paper sx={{ mb: 3 }}>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab
                icon={<List />}
                iconPosition="start"
                label="Logs"
                value={0}
              />
              <Tab
                icon={<BarChart />}
                iconPosition="start"
                label="Metrics"
                value={1}
                disabled={metricsAvailable === false}
              />
            </Tabs>
          </Paper>

          {/* Content */}
          <Grid container spacing={3}>
            {tabValue === 0 && (
              <Grid item xs={12}>
                <LogViewer
                  serviceId={selectedService}
                  namespace={selectedNamespace || undefined}
                  onServiceChange={handleServiceChange}
                />
              </Grid>
            )}
            {tabValue === 1 && (
              <Grid item xs={12}>
                <MetricsChart
                  serviceId={selectedService}
                  namespace={selectedNamespace || undefined}
                  onServiceChange={handleServiceChange}
                />
              </Grid>
            )}
          </Grid>
        </>
      )}
    </Box>
  )
}

export default ObservabilityPage
