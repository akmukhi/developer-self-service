import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Button,
} from '@mui/material'
import { Folder, Delete, Refresh, AccessTime, Schedule } from '@mui/icons-material'
import { format, formatDistanceToNow, isPast } from 'date-fns'
import type { Environment } from '../types'
import { EnvironmentStatus } from '../types'

interface EnvironmentCardProps {
  environment: Environment
  onRefresh?: () => void
  onDelete?: () => void
}

const getStatusColor = (
  status: string | EnvironmentStatus
): 'default' | 'primary' | 'success' | 'error' | 'warning' => {
  const statusStr = String(status).toLowerCase()
  switch (statusStr) {
    case 'active':
      return 'success'
    case 'creating':
    case 'expiring':
      return 'warning'
    case 'expired':
    case 'deleted':
      return 'error'
    default:
      return 'default'
  }
}

const EnvironmentCard = ({ environment, onRefresh, onDelete }: EnvironmentCardProps) => {
  const expiresAt = new Date(environment.expires_at)
  const isExpired = isPast(expiresAt)
  const timeUntilExpiry = formatDistanceToNow(expiresAt, { addSuffix: true })
  const timeRemaining = Math.max(0, expiresAt.getTime() - Date.now())
  const totalTime = environment.ttl_hours * 60 * 60 * 1000
  const progress = totalTime > 0 ? ((totalTime - timeRemaining) / totalTime) * 100 : 0

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s, box-shadow 0.2s',
        border: isExpired ? '2px solid' : 'none',
        borderColor: isExpired ? 'error.main' : 'transparent',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 4,
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <Folder color="primary" />
            <Box>
              <Typography variant="h6" component="h2">
                {environment.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {environment.namespace}
              </Typography>
            </Box>
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
              <Tooltip title="Delete Environment">
                <IconButton size="small" color="error" onClick={onDelete}>
                  <Delete fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>

        {/* Status */}
        <Box mb={2}>
          <Chip
            label={String(environment.status).toUpperCase()}
            color={getStatusColor(environment.status)}
            size="small"
            sx={{ mb: 1 }}
          />
          {isExpired && (
            <Chip
              label="Expired"
              color="error"
              size="small"
              sx={{ ml: 1 }}
            />
          )}
        </Box>

        {/* TTL Progress */}
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Box display="flex" alignItems="center" gap={0.5}>
              <AccessTime fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                Time Remaining
              </Typography>
            </Box>
            <Typography variant="body2" fontWeight="medium" color={isExpired ? 'error.main' : 'text.primary'}>
              {isExpired ? 'Expired' : timeUntilExpiry}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={Math.min(progress, 100)}
            color={isExpired ? 'error' : progress > 80 ? 'warning' : 'success'}
            sx={{ height: 8, borderRadius: 1 }}
          />
          <Box display="flex" justifyContent="space-between" mt={0.5}>
            <Typography variant="caption" color="text.secondary">
              TTL: {environment.ttl_hours} hours
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Expires: {format(expiresAt, 'PPp')}
            </Typography>
          </Box>
        </Box>

        {/* Services */}
        {environment.services.length > 0 && (
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Services ({environment.services.length})
            </Typography>
            <Box display="flex" gap={0.5} flexWrap="wrap">
              {environment.services.map((serviceId) => (
                <Chip
                  key={serviceId}
                  label={serviceId}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Labels */}
        {Object.keys(environment.labels).length > 0 && (
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Labels
            </Typography>
            <Box display="flex" gap={0.5} flexWrap="wrap">
              {Object.entries(environment.labels).map(([key, value]) => (
                <Chip
                  key={key}
                  label={`${key}=${value}`}
                  size="small"
                  variant="outlined"
                  color="primary"
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Timestamps */}
        <Box mt="auto">
          <Typography variant="caption" color="text.secondary" display="block">
            Created: {format(new Date(environment.created_at), 'PPp')}
          </Typography>
          {environment.deleted_at && (
            <Typography variant="caption" color="error" display="block">
              Deleted: {format(new Date(environment.deleted_at), 'PPp')}
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  )
}

export default EnvironmentCard

