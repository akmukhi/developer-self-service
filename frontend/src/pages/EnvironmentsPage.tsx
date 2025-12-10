import { useState, useEffect } from 'react'
import {
  Typography,
  Box,
  Button,
  Grid,
  Alert,
  CircularProgress,
  TextField,
  InputAdornment,
  Paper,
  Tabs,
  Tab,
} from '@mui/material'
import { Add, Search, Refresh, Delete } from '@mui/icons-material'
import EnvironmentRequest from '../components/EnvironmentRequest'
import EnvironmentCard from '../components/EnvironmentCard'
import { api } from '../services/api'
import type { Environment, EnvironmentCreateRequest, EnvironmentStatus } from '../types'

const EnvironmentsPage = () => {
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [namespaceFilter, setNamespaceFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [tabValue, setTabValue] = useState(0)
  const [availableServices, setAvailableServices] = useState<string[]>([])

  const fetchEnvironments = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.environments.list(
        namespaceFilter || undefined,
        statusFilter !== 'all' ? (statusFilter as EnvironmentStatus) : undefined
      )
      setEnvironments(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch environments')
      console.error('Error fetching environments:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchServices = async () => {
    try {
      const services = await api.services.list()
      setAvailableServices(services.map((s) => s.id))
    } catch (err) {
      console.error('Error fetching services:', err)
    }
  }

  useEffect(() => {
    fetchEnvironments()
    fetchServices()
  }, [namespaceFilter, statusFilter])

  const handleCreateEnvironment = async (data: EnvironmentCreateRequest) => {
    try {
      await api.environments.create(data)
      await fetchEnvironments() // Refresh the list
    } catch (err) {
      throw err // Re-throw to let EnvironmentRequest handle the error
    }
  }

  const handleDeleteEnvironment = async (environmentId: string) => {
    if (!window.confirm('Are you sure you want to delete this environment? This action cannot be undone.')) {
      return
    }

    try {
      await api.environments.delete(environmentId)
      await fetchEnvironments() // Refresh the list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete environment')
      console.error('Error deleting environment:', err)
    }
  }

  const handleRefresh = async () => {
    await fetchEnvironments()
    await fetchServices()
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
    if (newValue === 0) {
      setStatusFilter('all')
    } else if (newValue === 1) {
      setStatusFilter('active')
    } else if (newValue === 2) {
      setStatusFilter('expired')
    } else if (newValue === 3) {
      setStatusFilter('deleted')
    }
  }

  const filteredEnvironments = environments.filter((environment) => {
    const matchesSearch =
      environment.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      environment.namespace.toLowerCase().includes(searchTerm.toLowerCase()) ||
      environment.services.some((s) => s.toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesStatus =
      statusFilter === 'all' ||
      String(environment.status).toLowerCase() === statusFilter.toLowerCase()

    return matchesSearch && matchesStatus
  })

  // Group environments by status for tabs
  const activeEnvironments = environments.filter(
    (e) => String(e.status).toLowerCase() === 'active'
  )
  const expiredEnvironments = environments.filter(
    (e) => String(e.status).toLowerCase() === 'expired'
  )
  const deletedEnvironments = environments.filter(
    (e) => String(e.status).toLowerCase() === 'deleted'
  )

  const getTabEnvironments = () => {
    switch (tabValue) {
      case 1:
        return activeEnvironments.filter((e) =>
          e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          e.namespace.toLowerCase().includes(searchTerm.toLowerCase())
        )
      case 2:
        return expiredEnvironments.filter((e) =>
          e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          e.namespace.toLowerCase().includes(searchTerm.toLowerCase())
        )
      case 3:
        return deletedEnvironments.filter((e) =>
          e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          e.namespace.toLowerCase().includes(searchTerm.toLowerCase())
        )
      default:
        return filteredEnvironments
    }
  }

  const displayEnvironments = tabValue === 0 ? filteredEnvironments : getTabEnvironments()

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
          Temporary Environments
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setFormOpen(true)}
          >
            Request Environment
          </Button>
        </Box>
      </Box>

      {/* Status Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label={`All (${environments.length})`} value={0} />
          <Tab label={`Active (${activeEnvironments.length})`} value={1} />
          <Tab label={`Expired (${expiredEnvironments.length})`} value={2} />
          <Tab label={`Deleted (${deletedEnvironments.length})`} value={3} />
        </Tabs>
      </Paper>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              size="small"
              label="Search Environments"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              placeholder="Search by name, namespace, or services"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              size="small"
              label="Filter by Namespace"
              value={namespaceFilter}
              onChange={(e) => setNamespaceFilter(e.target.value)}
              placeholder="e.g., dev-test-env"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && environments.length === 0 ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Environments Grid */}
          {displayEnvironments.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchTerm || namespaceFilter || tabValue > 0
                  ? 'No environments found matching your filters'
                  : 'No temporary environments found'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {searchTerm || namespaceFilter || tabValue > 0
                  ? 'Try adjusting your search or filter criteria'
                  : 'Request a temporary environment to get started'}
              </Typography>
              {!searchTerm && !namespaceFilter && tabValue === 0 && (
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => setFormOpen(true)}
                  sx={{ mt: 2 }}
                >
                  Request Environment
                </Button>
              )}
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {displayEnvironments.map((environment) => (
                <Grid item xs={12} sm={6} md={4} key={environment.id}>
                  <EnvironmentCard
                    environment={environment}
                    onRefresh={handleRefresh}
                    onDelete={() => handleDeleteEnvironment(environment.id)}
                  />
                </Grid>
              ))}
            </Grid>
          )}

          {/* Results Count */}
          {displayEnvironments.length > 0 && (
            <Box mt={3}>
              <Typography variant="body2" color="text.secondary">
                Showing {displayEnvironments.length} of {environments.length} environment(s)
              </Typography>
            </Box>
          )}
        </>
      )}

      {/* Create Environment Form */}
      <EnvironmentRequest
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleCreateEnvironment}
        availableServices={availableServices}
      />
    </Box>
  )
}

export default EnvironmentsPage
