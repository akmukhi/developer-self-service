import { useNavigate } from 'react-router-dom'
import {
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
} from '@mui/material'
import {
  CloudQueue,
  Storage,
  Folder,
  Lock,
  Assessment,
} from '@mui/icons-material'

const HomePage = () => {
  const navigate = useNavigate()

  const features = [
    {
      title: 'Services',
      description: 'Create and manage Kubernetes services',
      icon: <CloudQueue sx={{ fontSize: 40 }} />,
      path: '/services',
      color: '#1976d2',
    },
    {
      title: 'Deployments',
      description: 'View deployment status and history',
      icon: <Storage sx={{ fontSize: 40 }} />,
      path: '/deployments',
      color: '#2e7d32',
    },
    {
      title: 'Environments',
      description: 'Request and manage temporary environments',
      icon: <Folder sx={{ fontSize: 40 }} />,
      path: '/environments',
      color: '#ed6c02',
    },
    {
      title: 'Secrets',
      description: 'Rotate and manage service secrets',
      icon: <Lock sx={{ fontSize: 40 }} />,
      path: '/secrets',
      color: '#d32f2f',
    },
    {
      title: 'Observability',
      description: 'View logs and metrics for services',
      icon: <Assessment sx={{ fontSize: 40 }} />,
      path: '/observability',
      color: '#9c27b0',
    },
  ]

  return (
    <Box>
      <Typography variant="h3" component="h1" gutterBottom sx={{ mb: 4, fontWeight: 600 }}>
        Developer Self-Service Portal
      </Typography>
      <Typography variant="h6" color="text.secondary" paragraph sx={{ mb: 6 }}>
        Manage your services, deployments, environments, secrets, and observability
        from a single platform.
      </Typography>

      <Grid container spacing={3}>
        {features.map((feature) => (
          <Grid item xs={12} sm={6} md={4} key={feature.path}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box
                  sx={{
                    color: feature.color,
                    mb: 2,
                  }}
                >
                  {feature.icon}
                </Box>
                <Typography variant="h5" component="h2" gutterBottom>
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  onClick={() => navigate(feature.path)}
                  sx={{ color: feature.color }}
                >
                  Go to {feature.title}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default HomePage

