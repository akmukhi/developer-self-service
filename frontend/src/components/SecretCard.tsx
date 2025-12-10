import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
} from '@mui/material'
import { Lock, Refresh, History, ExpandMore, VisibilityOff } from '@mui/icons-material'
import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import type { Secret, SecretType } from '../types'
import { SecretType as SecretTypeEnum } from '../types'

interface SecretCardProps {
  secret: Secret
  onRotate?: () => void
  onRefresh?: () => void
}

const getSecretTypeLabel = (type: string | SecretType): string => {
  const typeStr = String(type)
  switch (typeStr) {
    case SecretTypeEnum.OPAQUE:
      return 'Opaque'
    case SecretTypeEnum.TLS:
      return 'TLS'
    case SecretTypeEnum.DOCKER_CONFIG:
      return 'Docker Config'
    case SecretTypeEnum.BASIC_AUTH:
      return 'Basic Auth'
    case SecretTypeEnum.SSH_AUTH:
      return 'SSH Auth'
    default:
      return typeStr
  }
}

const SecretCard = ({ secret, onRotate, onRefresh }: SecretCardProps) => {
  const navigate = useNavigate()

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
            <Lock color="primary" />
            <Box>
              <Typography variant="h6" component="h2">
                {secret.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {secret.namespace}
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
          </Box>
        </Box>

        {/* Secret Type */}
        <Box mb={2}>
          <Chip
            label={getSecretTypeLabel(secret.secret_type)}
            size="small"
            variant="outlined"
            sx={{ mb: 1 }}
          />
        </Box>

        {/* Service Link */}
        <Box mb={2}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Service
          </Typography>
          <Button
            size="small"
            onClick={() => navigate(`/services?service_id=${secret.service_id}`)}
            sx={{ textTransform: 'none', p: 0, minWidth: 'auto' }}
          >
            {secret.service_id}
          </Button>
        </Box>

        {/* Secret Keys */}
        <Box mb={2}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Secret Keys ({secret.keys.length})
          </Typography>
          {secret.keys.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              No keys configured
            </Typography>
          ) : (
            <Box display="flex" gap={0.5} flexWrap="wrap">
              {secret.keys.map((key) => (
                <Chip
                  key={key}
                  label={key}
                  size="small"
                  variant="outlined"
                  icon={<VisibilityOff fontSize="small" />}
                />
              ))}
            </Box>
          )}
        </Box>

        {/* Last Rotated */}
        {secret.last_rotated && (
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Last Rotated
            </Typography>
            <Typography variant="body2">
              {format(new Date(secret.last_rotated), 'PPp')}
            </Typography>
          </Box>
        )}

        {/* Rotation History */}
        {secret.rotation_history.length > 0 && (
          <Accordion sx={{ mb: 2 }}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box display="flex" alignItems="center" gap={1}>
                <History fontSize="small" />
                <Typography variant="body2">
                  Rotation History ({secret.rotation_history.length})
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <List dense>
                {secret.rotation_history
                  .slice()
                  .reverse()
                  .map((history, index) => (
                    <ListItem key={index} disablePadding>
                      <ListItemText
                        primary={
                          <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="body2">
                              Version {history.version}
                            </Typography>
                            <Chip
                              label={format(new Date(history.rotated_at), 'PPp')}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        }
                        secondary={
                          history.rotated_by && (
                            <Typography variant="caption" color="text.secondary">
                              Rotated by: {history.rotated_by}
                            </Typography>
                          )
                        }
                      />
                    </ListItem>
                  ))}
              </List>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Rotate Button */}
        <Box mt="auto">
          <Button
            fullWidth
            variant="contained"
            startIcon={<Refresh />}
            onClick={onRotate}
            disabled={secret.keys.length === 0}
          >
            Rotate Secrets
          </Button>
        </Box>

        {/* Timestamps */}
        <Box mt={2}>
          <Typography variant="caption" color="text.secondary" display="block">
            Created: {format(new Date(secret.created_at), 'PPp')}
          </Typography>
          {secret.updated_at && (
            <Typography variant="caption" color="text.secondary" display="block">
              Updated: {format(new Date(secret.updated_at), 'PPp')}
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  )
}

export default SecretCard

