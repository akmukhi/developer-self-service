import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import ServicesPage from './pages/ServicesPage'
import DeploymentsPage from './pages/DeploymentsPage'
import EnvironmentsPage from './pages/EnvironmentsPage'
import SecretsPage from './pages/SecretsPage'
import ObservabilityPage from './pages/ObservabilityPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/services" element={<ServicesPage />} />
        <Route path="/deployments" element={<DeploymentsPage />} />
        <Route path="/environments" element={<EnvironmentsPage />} />
        <Route path="/secrets" element={<SecretsPage />} />
        <Route path="/observability" element={<ObservabilityPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default App

