import { Routes, Route } from 'react-router-dom'
import { Container } from '@mui/material'
import Layout from './components/Layout'
import ServicesPage from './pages/ServicesPage'
import DeploymentsPage from './pages/DeploymentsPage'
import EnvironmentsPage from './pages/EnvironmentsPage'
import SecretsPage from './pages/SecretsPage'
import ObservabilityPage from './pages/ObservabilityPage'

function App() {
  return (
    <Layout>
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Routes>
          <Route path="/" element={<ServicesPage />} />
          <Route path="/services" element={<ServicesPage />} />
          <Route path="/deployments" element={<DeploymentsPage />} />
          <Route path="/environments" element={<EnvironmentsPage />} />
          <Route path="/secrets" element={<SecretsPage />} />
          <Route path="/observability" element={<ObservabilityPage />} />
        </Routes>
      </Container>
    </Layout>
  )
}

export default App

