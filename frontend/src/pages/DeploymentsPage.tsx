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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import { Search, Refresh, FilterList } from '@mui/icons-material'
import DeploymentCard from '../components/DeploymentCard'
import { api } from '../services/api'
import type { Deployment, DeploymentStatus } from '../types'

const DeploymentsPage = () => {
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [namespaceFilter, setNamespaceFilter] = useState('')
  const [serviceFilter, setServiceFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [tabValue, setTabValue] = useState(0)

  const fetchDeployments = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.deployments.list(
        namespaceFilter || undefined,
        serviceFilter || undefined
      )
      setDeployments(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch deployments')
      console.error('Error fetching deployments:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDeployments()
  }, [namespaceFilter, serviceFilter])

  const handleRefresh = async () => {
    await fetchDeployments()
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
    if (newValue === 0) {
      setStatusFilter('all')
    } else if (newValue === 1) {
      setStatusFilter('available')
    } else if (newValue === 2) {
      setStatusFilter('progressing')
    } else if (newValue === 3) {
      setStatusFilter('failed')
    }
  }

  const filteredDeployments = deployments.filter((deployment) => {
    // Search filter
    const matchesSearch =
      deployment.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      deployment.image.toLowerCase().includes(searchTerm.toLowerCase()) ||
      deployment.namespace.toLowerCase().includes(searchTerm.toLowerCase()) ||
      deployment.service_id.toLowerCase().includes(searchTerm.toLowerCase())

    // Status filter
    const matchesStatus =
      statusFilter === 'all' ||
      String(deployment.status).toLowerCase() === statusFilter.toLowerCase()

    return matchesSearch && matchesStatus
  })

  // Group deployments by status for tabs
  const availableDeployments = deployments.filter(
    (d) => String(d.status).toLowerCase() === 'available'
  )
  const progressingDeployments = deployments.filter(
    (d) => String(d.status).toLowerCase() === 'progressing'
  )
  const failedDeployments = deployments.filter(
    (d) => String(d.status).toLowerCase() === 'failed'
  )

  const getTabDeployments = () => {
    switch (tabValue) {
      case 1:
        return availableDeployments.filter((d) =>
          d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          d.image.toLowerCase().includes(searchTerm.toLowerCase()) ||
          d.namespace.toLowerCase().includes(searchTerm.toLowerCase())
        )
      case 2:
        return progressingDeployments.filter((d) =>
          d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          d.image.toLowerCase().includes(searchTerm.toLowerCase()) ||
          d.namespace.toLowerCase().includes(searchTerm.toLowerCase())
        )
      case 3:
        return failedDeployments.filter((d) =>
          d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          d.image.toLowerCase().includes(searchTerm.toLowerCase()) ||
          d.namespace.toLowerCase().includes(searchTerm.toLowerCase())
        )
      default:
        return filteredDeployments
    }
  }

  const displayDeployments = tabValue === 0 ? filteredDeployments : getTabDeployments()

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
          Deployments
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Status Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab
            label={`All (${deployments.length})`}
            value={0}
          />
          <Tab
            label={`Available (${availableDeployments.length})`}
            value={1}
          />
          <Tab
            label={`Progressing (${progressingDeployments.length})`}
            value={2}
          />
          <Tab
            label={`Failed (${failedDeployments.length})`}
            value={3}
          />
        </Tabs>
      </Paper>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              size="small"
              label="Search Deployments"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              placeholder="Search by name, image, namespace, or service"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              size="small"
              label="Filter by Namespace"
              value={namespaceFilter}
              onChange={(e) => setNamespaceFilter(e.target.value)}
              placeholder="e.g., default, production"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              size="small"
              label="Filter by Service ID"
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
              placeholder="e.g., default/my-service"
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
      {loading && deployments.length === 0 ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Deployments Grid */}
          {displayDeployments.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchTerm || namespaceFilter || serviceFilter || tabValue > 0
                  ? 'No deployments found matching your filters'
                  : 'No deployments found'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {searchTerm || namespaceFilter || serviceFilter || tabValue > 0
                  ? 'Try adjusting your search or filter criteria'
                  : 'Deployments will appear here once services are created'}
              </Typography>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {displayDeployments.map((deployment) => (
                <Grid item xs={12} sm={6} md={4} key={deployment.id}>
                  <DeploymentCard
                    deployment={deployment}
                    onRefresh={handleRefresh}
                  />
                </Grid>
              ))}
            </Grid>
          )}

          {/* Results Count */}
          {displayDeployments.length > 0 && (
            <Box mt={3}>
              <Typography variant="body2" color="text.secondary">
                Showing {displayDeployments.length} of {deployments.length} deployment(s)
              </Typography>
            </Box>
          )}
        </>
      )}
    </Box>
  )
}

export default DeploymentsPage
