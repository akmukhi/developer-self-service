import { Card, CardContent, Typography, Box, Chip, IconButton, Tooltip } from '@mui/material'
import { CloudQueue, Delete, Refresh } from '@mui/icons-material'
import { format } from 'date-fns'
import type { Service } from '../types'

interface ServiceCardProps {
  service: Service
  onRefresh?: () => void
  onDelete?: () => void
}

const getStatusColor = (status: string | number | Service): 'default' | 'primary' | 'success' | 'error' | 'warning' => {
  const statusStr = String(status).toLowerCase()
  switch (statusStr) {
    case 'running':
      return 'success'
    case 'creating':
    case 'pending':
      return 'warning'
    case 'failed':
      return 'error'
    case 'stopped':
      return 'default'
    default:
      return 'default'
  }
}

const ServiceCard = ({ service, onRefresh, onDelete }: ServiceCardProps) => {
  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 4,
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <CloudQueue color="primary" />
            <Typography variant="h6" component="h2">
              {service.name}
            </Typography>
          </Box>
          <Box display="flex" gap={1}>
            {onRefresh && (
              <Tooltip title="Refresh">
                <IconButton size="small" onClick={onRefresh}>
                  <Refresh fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {onDelete && (
              <Tooltip title="Delete">
                <IconButton size="small" color="error" onClick={onDelete}>
                  <Delete fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>

        <Box mb={2}>
          <Chip
            label={String(service.status).toUpperCase()}
            color={getStatusColor(service.status)}
            size="small"
            sx={{ mb: 1 }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Namespace: {service.namespace}
          </Typography>
        </Box>

        <Box mb={2}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Image
          </Typography>
          <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
            {service.image}
          </Typography>
        </Box>

        <Box display="flex" gap={2} mb={2}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Replicas
            </Typography>
            <Typography variant="body1" fontWeight="medium">
              {service.replicas}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              CPU
            </Typography>
            <Typography variant="body1" fontWeight="medium">
              {service.resources.cpu}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Memory
            </Typography>
            <Typography variant="body1" fontWeight="medium">
              {service.resources.memory}
            </Typography>
          </Box>
        </Box>

        {service.ports.length > 0 && (
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Ports
            </Typography>
            <Box display="flex" gap={0.5} flexWrap="wrap">
              {service.ports.map((port) => (
                <Chip key={port} label={port} size="small" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {Object.keys(service.env_vars).length > 0 && (
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Environment Variables
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
              {Object.keys(service.env_vars).length} variable(s) configured
            </Typography>
          </Box>
        )}

        <Box mt="auto">
          <Typography variant="caption" color="text.secondary">
            Created: {format(new Date(service.created_at), 'PPp')}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  )
}

export default ServiceCard

