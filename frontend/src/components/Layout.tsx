import { ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
} from '@mui/material'
import {
  CloudQueue,
  Storage,
  Folder,
  Lock,
  Assessment,
} from '@mui/icons-material'

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const navigate = useNavigate()
  const location = useLocation()

  const navItems = [
    { label: 'Services', path: '/services', icon: <CloudQueue /> },
    { label: 'Deployments', path: '/deployments', icon: <Storage /> },
    { label: 'Environments', path: '/environments', icon: <Folder /> },
    { label: 'Secrets', path: '/secrets', icon: <Lock /> },
    { label: 'Observability', path: '/observability', icon: <Assessment /> },
  ]

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, cursor: 'pointer' }}
            onClick={() => navigate('/')}
          >
            Developer Self-Service Portal
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {navItems.map((item) => (
              <Button
                key={item.path}
                color="inherit"
                startIcon={item.icon}
                onClick={() => navigate(item.path)}
                variant={location.pathname === item.path ? 'outlined' : 'text'}
              >
                {item.label}
              </Button>
            ))}
          </Box>
        </Toolbar>
      </AppBar>
      <Box component="main" sx={{ flexGrow: 1 }}>
        {children}
      </Box>
    </Box>
  )
}

export default Layout

