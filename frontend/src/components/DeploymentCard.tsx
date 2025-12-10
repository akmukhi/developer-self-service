import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Link,
} from '@mui/material'
import { Storage, Refresh, OpenInNew } from '@mui/icons-material'
import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import type { Deployment } from '../types'
import { DeploymentStatus } from '../types'

interface DeploymentCardProps {
  deployment: Deployment
  onRefresh?: () => void
}

const getStatusColor = (
  status: string | DeploymentStatus
): 'default' | 'primary' | 'success' | 'error' | 'warning' => {
  const statusStr = String(status).toLowerCase()
  switch (statusStr) {
    case 'available':
      return 'success'
    case 'progressing':
      return 'warning'
    case 'pending':
      return 'default'
    case 'failed':
      return 'error'
    case 'unknown':
      return 'default'
    default:
      return 'default'
  }
}

const DeploymentCard = ({ deployment, onRefresh }: DeploymentCardProps) => {
  const navigate = useNavigate()

  const replicaProgress =
    deployment.replicas.desired > 0
      ? (deployment.replicas.ready / deployment.replicas.desired) * 100
      : 0

  const isHealthy =
    deployment.replicas.ready === deployment.replicas.desired &&
    deployment.replicas.desired > 0

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
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <Storage color="primary" />
            <Box>
              <Typography variant="h6" component="h2">
                {deployment.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {deployment.namespace}
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
            <Tooltip title="View Service">
              <IconButton
                size="small"
                onClick={() => navigate(`/services?service_id=${deployment.service_id}`)}
              >
                <OpenInNew fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Status */}
        <Box mb={2}>
          <Chip
            label={String(deployment.status).toUpperCase()}
            color={getStatusColor(deployment.status)}
            size="small"
            sx={{ mb: 1 }}
          />
          {isHealthy && (
            <Chip
              label="Healthy"
              color="success"
              size="small"
              sx={{ ml: 1 }}
            />
          )}
        </Box>

        {/* Image Info */}
        <Box mb={2}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Image
          </Typography>
          <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
            {deployment.image}
          </Typography>
          {deployment.image_tag && (
            <Chip
              label={`Tag: ${deployment.image_tag}`}
              size="small"
              variant="outlined"
              sx={{ mt: 0.5 }}
            />
          )}
        </Box>

        {/* Pod Replicas */}
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" color="text.secondary">
              Pod Replicas
            </Typography>
            <Typography variant="body2" fontWeight="medium">
              {deployment.replicas.ready} / {deployment.replicas.desired}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={replicaProgress}
            color={isHealthy ? 'success' : 'warning'}
            sx={{ height: 8, borderRadius: 1 }}
          />
          <Box display="flex" gap={2} mt={1}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Ready
              </Typography>
              <Typography variant="body2" fontWeight="medium" color="success.main">
                {deployment.replicas.ready}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Available
              </Typography>
              <Typography variant="body2" fontWeight="medium" color="info.main">
                {deployment.replicas.available}
              </Typography>
            </Box>
            {deployment.replicas.unavailable > 0 && (
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Unavailable
                </Typography>
                <Typography variant="body2" fontWeight="medium" color="error.main">
                  {deployment.replicas.unavailable}
                </Typography>
              </Box>
            )}
          </Box>
        </Box>

        {/* Service Link */}
        <Box mb={2}>
          <Link
            component="button"
            variant="body2"
            onClick={() => navigate(`/services?service_id=${deployment.service_id}`)}
            sx={{ textDecoration: 'none' }}
          >
            View Service: {deployment.service_id}
          </Link>
        </Box>

        {/* Timestamps */}
        <Box mt="auto">
          <Typography variant="caption" color="text.secondary" display="block">
            Created: {format(new Date(deployment.created_at), 'PPp')}
          </Typography>
          {deployment.updated_at && (
            <Typography variant="caption" color="text.secondary" display="block">
              Updated: {format(new Date(deployment.updated_at), 'PPp')}
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  )
}

export default DeploymentCard

