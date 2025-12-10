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
} from '@mui/material'
import { Add, Search, Refresh } from '@mui/icons-material'
import ServiceForm from '../components/ServiceForm'
import ServiceCard from '../components/ServiceCard'
import { api } from '../services/api'
import type { Service, ServiceCreateRequest } from '../types'

const ServicesPage = () => {
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [namespaceFilter, setNamespaceFilter] = useState('')

  const fetchServices = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.services.list(namespaceFilter || undefined)
      setServices(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch services')
      console.error('Error fetching services:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchServices()
  }, [namespaceFilter])

  const handleCreateService = async (data: ServiceCreateRequest) => {
    try {
      await api.services.create(data)
      await fetchServices() // Refresh the list
    } catch (err) {
      throw err // Re-throw to let ServiceForm handle the error
    }
  }

  const handleRefresh = async () => {
    await fetchServices()
  }

  const filteredServices = services.filter((service) => {
    const matchesSearch =
      service.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      service.image.toLowerCase().includes(searchTerm.toLowerCase()) ||
      service.namespace.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
          Services
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
            Create Service
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              size="small"
              label="Search Services"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              placeholder="Search by name, image, or namespace"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              size="small"
              label="Filter by Namespace"
              value={namespaceFilter}
              onChange={(e) => setNamespaceFilter(e.target.value)}
              placeholder="e.g., default, production"
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
      {loading && services.length === 0 ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Services Grid */}
          {filteredServices.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchTerm || namespaceFilter
                  ? 'No services found matching your filters'
                  : 'No services found'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {searchTerm || namespaceFilter
                  ? 'Try adjusting your search or filter criteria'
                  : 'Create your first service to get started'}
              </Typography>
              {!searchTerm && !namespaceFilter && (
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => setFormOpen(true)}
                  sx={{ mt: 2 }}
                >
                  Create Service
                </Button>
              )}
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {filteredServices.map((service) => (
                <Grid item xs={12} sm={6} md={4} key={service.id}>
                  <ServiceCard
                    service={service}
                    onRefresh={handleRefresh}
                  />
                </Grid>
              ))}
            </Grid>
          )}

          {/* Results Count */}
          {filteredServices.length > 0 && (
            <Box mt={3}>
              <Typography variant="body2" color="text.secondary">
                Showing {filteredServices.length} of {services.length} service(s)
              </Typography>
            </Box>
          )}
        </>
      )}

      {/* Create Service Form */}
      <ServiceForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleCreateService}
      />
    </Box>
  )
}

export default ServicesPage
