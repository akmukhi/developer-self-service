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
import { Search, Refresh } from '@mui/icons-material'
import SecretCard from '../components/SecretCard'
import SecretRotator from '../components/SecretRotator'
import { api } from '../services/api'
import type { Secret, SecretRotateRequest } from '../types'

const SecretsPage = () => {
  const [secrets, setSecrets] = useState<Secret[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [namespaceFilter, setNamespaceFilter] = useState('')
  const [serviceFilter, setServiceFilter] = useState('')
  const [rotatorOpen, setRotatorOpen] = useState(false)
  const [selectedSecret, setSelectedSecret] = useState<Secret | null>(null)

  const fetchSecrets = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.secrets.list(
        namespaceFilter || undefined,
        serviceFilter || undefined
      )
      setSecrets(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch secrets')
      console.error('Error fetching secrets:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSecrets()
  }, [namespaceFilter, serviceFilter])

  const handleRotate = async (serviceId: string, data: SecretRotateRequest) => {
    try {
      await api.secrets.rotate(serviceId, data)
      await fetchSecrets() // Refresh the list
    } catch (err) {
      throw err // Re-throw to let SecretRotator handle the error
    }
  }

  const handleOpenRotator = (secret: Secret) => {
    setSelectedSecret(secret)
    setRotatorOpen(true)
  }

  const handleCloseRotator = () => {
    setRotatorOpen(false)
    setSelectedSecret(null)
  }

  const handleRefresh = async () => {
    await fetchSecrets()
  }

  const filteredSecrets = secrets.filter((secret) => {
    const matchesSearch =
      secret.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      secret.service_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      secret.namespace.toLowerCase().includes(searchTerm.toLowerCase()) ||
      secret.keys.some((key) => key.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
            Secrets
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Manage and rotate secrets for your services
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Security Notice */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Security Notice:</strong> Secret values are never displayed for security reasons.
          Only metadata, keys, and rotation history are shown.
        </Typography>
      </Alert>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              size="small"
              label="Search Secrets"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              placeholder="Search by name, service, namespace, or keys"
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
      {loading && secrets.length === 0 ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Secrets Grid */}
          {filteredSecrets.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchTerm || namespaceFilter || serviceFilter
                  ? 'No secrets found matching your filters'
                  : 'No secrets found'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {searchTerm || namespaceFilter || serviceFilter
                  ? 'Try adjusting your search or filter criteria'
                  : 'Secrets are automatically created when services are created'}
              </Typography>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {filteredSecrets.map((secret) => (
                <Grid item xs={12} sm={6} md={4} key={secret.id}>
                  <SecretCard
                    secret={secret}
                    onRotate={() => handleOpenRotator(secret)}
                    onRefresh={handleRefresh}
                  />
                </Grid>
              ))}
            </Grid>
          )}

          {/* Results Count */}
          {filteredSecrets.length > 0 && (
            <Box mt={3}>
              <Typography variant="body2" color="text.secondary">
                Showing {filteredSecrets.length} of {secrets.length} secret(s)
              </Typography>
            </Box>
          )}
        </>
      )}

      {/* Secret Rotator Dialog */}
      <SecretRotator
        open={rotatorOpen}
        onClose={handleCloseRotator}
        secret={selectedSecret}
        onRotate={handleRotate}
      />
    </Box>
  )
}

export default SecretsPage
