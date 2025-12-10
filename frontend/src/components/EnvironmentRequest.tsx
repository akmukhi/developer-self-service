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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
} from '@mui/material'
import { Close, Add, Delete } from '@mui/icons-material'
import type { EnvironmentCreateRequest } from '../types'

interface EnvironmentRequestProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: EnvironmentCreateRequest) => Promise<void>
  availableServices?: string[]
}

interface Label {
  key: string
  value: string
}

const EnvironmentRequest = ({
  open,
  onClose,
  onSubmit,
  availableServices = [],
}: EnvironmentRequestProps) => {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState<EnvironmentCreateRequest>({
    name: '',
    ttl_hours: 24,
    namespace: undefined,
    services: [],
    labels: {},
  })
  const [labels, setLabels] = useState<Label[]>([])
  const [selectedServices, setSelectedServices] = useState<string[]>([])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Convert labels array to object
      const labelsObj: Record<string, string> = {}
      labels.forEach(({ key, value }) => {
        if (key && value) {
          labelsObj[key] = value
        }
      })

      const submitData: EnvironmentCreateRequest = {
        ...formData,
        services: selectedServices.length > 0 ? selectedServices : undefined,
        labels: Object.keys(labelsObj).length > 0 ? labelsObj : undefined,
      }

      await onSubmit(submitData)

      // Reset form
      setFormData({
        name: '',
        ttl_hours: 24,
        namespace: undefined,
        services: [],
        labels: {},
      })
      setLabels([])
      setSelectedServices([])
      onClose()
    } catch (error) {
      console.error('Error creating environment:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddLabel = () => {
    setLabels([...labels, { key: '', value: '' }])
  }

  const handleRemoveLabel = (index: number) => {
    setLabels(labels.filter((_, i) => i !== index))
  }

  const handleLabelChange = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...labels]
    updated[index] = { ...updated[index], [field]: value }
    setLabels(updated)
  }

  const ttlOptions = [
    { value: 1, label: '1 hour' },
    { value: 6, label: '6 hours' },
    { value: 12, label: '12 hours' },
    { value: 24, label: '24 hours (1 day)' },
    { value: 48, label: '48 hours (2 days)' },
    { value: 72, label: '72 hours (3 days)' },
    { value: 168, label: '168 hours (7 days)' },
  ]

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Request Temporary Environment</Typography>
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
                label="Environment Name"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                helperText="Name for your temporary environment"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Time to Live (TTL)</InputLabel>
                <Select
                  value={formData.ttl_hours}
                  label="Time to Live (TTL)"
                  onChange={(e) =>
                    setFormData({ ...formData, ttl_hours: e.target.value as number })
                  }
                >
                  {ttlOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Custom Namespace (Optional)"
                value={formData.namespace || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    namespace: e.target.value || undefined,
                  })
                }
                helperText="Leave empty to auto-generate namespace name"
              />
            </Grid>

            {/* Services to Deploy */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                Services to Deploy (Optional)
              </Typography>
              <Autocomplete
                multiple
                freeSolo
                options={availableServices}
                value={selectedServices}
                onChange={(_event, newValue) => {
                  setSelectedServices(newValue)
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Service IDs"
                    helperText="Enter service IDs (e.g., default/my-service)"
                    placeholder="default/my-service"
                  />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      variant="outlined"
                      label={option}
                      {...getTagProps({ index })}
                      key={index}
                    />
                  ))
                }
              />
            </Grid>

            {/* Labels */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Labels (Optional)
                </Typography>
                <Button
                  startIcon={<Add />}
                  onClick={handleAddLabel}
                  size="small"
                  variant="outlined"
                >
                  Add Label
                </Button>
              </Box>
              {labels.map((label, index) => (
                <Grid container spacing={2} key={index} sx={{ mb: 2 }}>
                  <Grid item xs={5}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Key"
                      value={label.key}
                      onChange={(e) => handleLabelChange(index, 'key', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Value"
                      value={label.value}
                      onChange={(e) => handleLabelChange(index, 'value', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={1}>
                    <IconButton
                      onClick={() => handleRemoveLabel(index)}
                      color="error"
                      size="small"
                    >
                      <Delete />
                    </IconButton>
                  </Grid>
                </Grid>
              ))}
              {labels.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  No labels added
                </Typography>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={loading || !formData.name}>
            {loading ? 'Creating...' : 'Create Environment'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  )
}

export default EnvironmentRequest

