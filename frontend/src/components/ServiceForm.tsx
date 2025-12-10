import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  Box,
  Typography,
  IconButton,
  Chip,
  Divider,
} from '@mui/material'
import { Add, Delete, Close } from '@mui/icons-material'
import type { ServiceCreateRequest } from '../types'

interface ServiceFormProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: ServiceCreateRequest) => Promise<void>
}

interface EnvVar {
  key: string
  value: string
}

const ServiceForm = ({ open, onClose, onSubmit }: ServiceFormProps) => {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState<ServiceCreateRequest>({
    name: '',
    image: '',
    replicas: 1,
    namespace: 'default',
    resources: {
      cpu: '100m',
      memory: '128Mi',
    },
    env_vars: {},
    ports: [],
  })
  const [envVars, setEnvVars] = useState<EnvVar[]>([])
  const [ports, setPorts] = useState<string[]>([''])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Convert env vars array to object
      const envVarsObj: Record<string, string> = {}
      envVars.forEach(({ key, value }) => {
        if (key && value) {
          envVarsObj[key] = value
        }
      })

      // Convert ports array to numbers
      const portsArray = ports
        .map((p) => parseInt(p, 10))
        .filter((p) => !isNaN(p) && p > 0)

      const submitData: ServiceCreateRequest = {
        ...formData,
        env_vars: envVarsObj,
        ports: portsArray.length > 0 ? portsArray : undefined,
      }

      await onSubmit(submitData)
      
      // Reset form
      setFormData({
        name: '',
        image: '',
        replicas: 1,
        namespace: 'default',
        resources: {
          cpu: '100m',
          memory: '128Mi',
        },
        env_vars: {},
        ports: [],
      })
      setEnvVars([])
      setPorts([''])
      onClose()
    } catch (error) {
      console.error('Error creating service:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddEnvVar = () => {
    setEnvVars([...envVars, { key: '', value: '' }])
  }

  const handleRemoveEnvVar = (index: number) => {
    setEnvVars(envVars.filter((_, i) => i !== index))
  }

  const handleEnvVarChange = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...envVars]
    updated[index] = { ...updated[index], [field]: value }
    setEnvVars(updated)
  }

  const handleAddPort = () => {
    setPorts([...ports, ''])
  }

  const handleRemovePort = (index: number) => {
    setPorts(ports.filter((_, i) => i !== index))
  }

  const handlePortChange = (index: number, value: string) => {
    const updated = [...ports]
    updated[index] = value
    setPorts(updated)
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Create New Service</Typography>
            <IconButton onClick={onClose} size="small">
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={3}>
            {/* Basic Information */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                Basic Information
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Service Name"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                helperText="Kubernetes-friendly name (lowercase, alphanumeric, hyphens)"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Container Image"
                required
                value={formData.image}
                onChange={(e) => setFormData({ ...formData, image: e.target.value })}
                helperText="e.g., nginx:latest, myapp:v1.0"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Namespace"
                value={formData.namespace}
                onChange={(e) => setFormData({ ...formData, namespace: e.target.value })}
                helperText="Kubernetes namespace"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Replicas"
                required
                value={formData.replicas}
                onChange={(e) =>
                  setFormData({ ...formData, replicas: parseInt(e.target.value, 10) || 1 })
                }
                inputProps={{ min: 1, max: 100 }}
                helperText="Number of pod replicas (1-100)"
              />
            </Grid>

            {/* Resource Requirements */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                Resource Requirements
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="CPU Request/Limit"
                value={formData.resources?.cpu || '100m'}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    resources: { ...formData.resources!, cpu: e.target.value },
                  })
                }
                helperText="e.g., 100m, 0.5, 1"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Memory Request/Limit"
                value={formData.resources?.memory || '128Mi'}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    resources: { ...formData.resources!, memory: e.target.value },
                  })
                }
                helperText="e.g., 128Mi, 512Mi, 1Gi"
              />
            </Grid>

            {/* Environment Variables */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Environment Variables
                </Typography>
                <Button
                  startIcon={<Add />}
                  onClick={handleAddEnvVar}
                  size="small"
                  variant="outlined"
                >
                  Add
                </Button>
              </Box>
              {envVars.map((envVar, index) => (
                <Grid container spacing={2} key={index} sx={{ mb: 2 }}>
                  <Grid item xs={5}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Key"
                      value={envVar.key}
                      onChange={(e) => handleEnvVarChange(index, 'key', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Value"
                      value={envVar.value}
                      onChange={(e) => handleEnvVarChange(index, 'value', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={1}>
                    <IconButton
                      onClick={() => handleRemoveEnvVar(index)}
                      color="error"
                      size="small"
                    >
                      <Delete />
                    </IconButton>
                  </Grid>
                </Grid>
              ))}
              {envVars.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  No environment variables added
                </Typography>
              )}
            </Grid>

            {/* Ports */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Container Ports
                </Typography>
                <Button
                  startIcon={<Add />}
                  onClick={handleAddPort}
                  size="small"
                  variant="outlined"
                >
                  Add
                </Button>
              </Box>
              {ports.map((port, index) => (
                <Grid container spacing={2} key={index} sx={{ mb: 2 }}>
                  <Grid item xs={11}>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="Port"
                      value={port}
                      onChange={(e) => handlePortChange(index, e.target.value)}
                      inputProps={{ min: 1, max: 65535 }}
                    />
                  </Grid>
                  <Grid item xs={1}>
                    <IconButton
                      onClick={() => handleRemovePort(index)}
                      color="error"
                      size="small"
                      disabled={ports.length === 1}
                    >
                      <Delete />
                    </IconButton>
                  </Grid>
                </Grid>
              ))}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={loading || !formData.name || !formData.image}>
            {loading ? 'Creating...' : 'Create Service'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  )
}

export default ServiceForm

