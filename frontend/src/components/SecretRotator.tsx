import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
  FormControlLabel,
  Checkbox,
  Chip,
  Divider,
  Alert,
} from '@mui/material'
import { Close, Lock, Refresh } from '@mui/icons-material'
import type { Secret, SecretRotateRequest } from '../types'

interface SecretRotatorProps {
  open: boolean
  onClose: () => void
  secret: Secret | null
  onRotate: (serviceId: string, data: SecretRotateRequest) => Promise<void>
}

const SecretRotator = ({ open, onClose, secret, onRotate }: SecretRotatorProps) => {
  const [loading, setLoading] = useState(false)
  const [selectedKeys, setSelectedKeys] = useState<string[]>([])
  const [updateDeployments, setUpdateDeployments] = useState(true)
  const [error, setError] = useState<string | null>(null)

  if (!secret) return null

  const handleToggleKey = (key: string) => {
    if (selectedKeys.includes(key)) {
      setSelectedKeys(selectedKeys.filter((k) => k !== key))
    } else {
      setSelectedKeys([...selectedKeys, key])
    }
  }

  const handleSelectAll = () => {
    if (selectedKeys.length === secret.keys.length) {
      setSelectedKeys([])
    } else {
      setSelectedKeys([...secret.keys])
    }
  }

  const handleSubmit = async () => {
    if (selectedKeys.length === 0 && secret.keys.length > 0) {
      setError('Please select at least one key to rotate, or select all keys')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const rotateData: SecretRotateRequest = {
        keys: selectedKeys.length > 0 ? selectedKeys : undefined, // If none selected, rotate all
        generate_new: true,
        update_deployments: updateDeployments,
      }

      await onRotate(secret.service_id, rotateData)
      
      // Reset form
      setSelectedKeys([])
      setUpdateDeployments(true)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rotate secrets')
      console.error('Error rotating secrets:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center" gap={1}>
            <Lock color="primary" />
            <Typography variant="h6">Rotate Secrets</Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box mb={3}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Service: {secret.service_id}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Secret: {secret.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Namespace: {secret.namespace}
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Select Keys to Rotate
            </Typography>
            <Button size="small" onClick={handleSelectAll}>
              {selectedKeys.length === secret.keys.length ? 'Deselect All' : 'Select All'}
            </Button>
          </Box>

          {secret.keys.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              No keys found in this secret
            </Typography>
          ) : (
            <Box display="flex" flexWrap="wrap" gap={1}>
              {secret.keys.map((key) => (
                <Chip
                  key={key}
                  label={key}
                  onClick={() => handleToggleKey(key)}
                  color={selectedKeys.includes(key) ? 'primary' : 'default'}
                  variant={selectedKeys.includes(key) ? 'filled' : 'outlined'}
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Box>
          )}
        </Box>

        <Box mb={2}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {selectedKeys.length === 0
              ? 'No keys selected. All keys will be rotated if you proceed.'
              : `${selectedKeys.length} key(s) selected for rotation.`}
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        <FormControlLabel
          control={
            <Checkbox
              checked={updateDeployments}
              onChange={(e) => setUpdateDeployments(e.target.checked)}
            />
          }
          label="Update deployments to use new secrets (rolling restart)"
        />
        <Typography variant="caption" color="text.secondary" display="block" sx={{ ml: 4, mt: 0.5 }}>
          This will trigger a rolling update for all deployments using this secret
        </Typography>

        {secret.last_rotated && (
          <Box mt={3}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Last Rotated: {new Date(secret.last_rotated).toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Rotation History: {secret.rotation_history.length} rotation(s)
            </Typography>
          </Box>
        )}

        <Alert severity="warning" sx={{ mt: 3 }}>
          <Typography variant="body2" fontWeight="medium">
            Warning: Rotating secrets will generate new values for the selected keys.
            Make sure your applications can handle the new secret values.
          </Typography>
        </Alert>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={handleSubmit}
          disabled={loading || secret.keys.length === 0}
          color="primary"
        >
          {loading ? 'Rotating...' : 'Rotate Secrets'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default SecretRotator

