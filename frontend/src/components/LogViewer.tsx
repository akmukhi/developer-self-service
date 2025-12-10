import { useState, useEffect, useRef } from 'react'
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  Search,
  Refresh,
  Download,
} from '@mui/icons-material'
import { api } from '../services/api'
import type { LogsResponse } from '../types'

interface LogViewerProps {
  serviceId: string
  namespace?: string
  onServiceChange?: (serviceId: string) => void
}

const LogViewer = ({ serviceId, namespace, onServiceChange }: LogViewerProps) => {
  const [logs, setLogs] = useState<LogsResponse | null>(null)
  const [aggregatedLogs, setAggregatedLogs] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lines, setLines] = useState(100)
  const [sinceMinutes, setSinceMinutes] = useState<number | undefined>(undefined)
  const [searchTerm, setSearchTerm] = useState('')
  const [viewMode, setViewMode] = useState<'per-pod' | 'aggregated'>('per-pod')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [autoRefreshInterval, setAutoRefreshInterval] = useState(30) // seconds
  const logContainerRef = useRef<HTMLDivElement>(null)

  const fetchLogs = async () => {
    if (!serviceId) return

    try {
      setLoading(true)
      setError(null)

      if (viewMode === 'aggregated') {
        const data = await api.observability.getAggregatedLogs(
          serviceId,
          lines,
          namespace
        )
        setAggregatedLogs(data.aggregated_logs)
      } else {
        const data = await api.observability.getLogs(serviceId, {
          lines,
          sinceMinutes,
          search: searchTerm || undefined,
          namespace,
        })
        setLogs(data)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs')
      console.error('Error fetching logs:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [serviceId, namespace, viewMode])

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchLogs()
      }, autoRefreshInterval * 1000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, autoRefreshInterval, serviceId, namespace, viewMode, lines, sinceMinutes, searchTerm])

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs, aggregatedLogs])

  const handleDownload = () => {
    const content = viewMode === 'aggregated' 
      ? aggregatedLogs 
      : logs?.pods.map(p => `[${p.pod}]\n${p.logs}`).join('\n\n') || ''
    
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs-${serviceId}-${new Date().toISOString()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const filteredLogs = logs?.pods.filter((pod) => {
    if (!searchTerm) return true
    return pod.logs.toLowerCase().includes(searchTerm.toLowerCase())
  })

  return (
    <Paper sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Logs
        </Typography>
        <Box display="flex" gap={1}>
          <Tooltip title="Auto-refresh">
            <Chip
              label={`Auto: ${autoRefreshInterval}s`}
              color={autoRefresh ? 'primary' : 'default'}
              onClick={() => setAutoRefresh(!autoRefresh)}
              size="small"
            />
          </Tooltip>
          <Tooltip title="Download Logs">
            <IconButton size="small" onClick={handleDownload}>
              <Download />
            </IconButton>
          </Tooltip>
          <IconButton size="small" onClick={fetchLogs} disabled={loading}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Controls */}
      <Box display="flex" gap={2} mb={2} flexWrap="wrap">
        <TextField
          size="small"
          label="Lines"
          type="number"
          value={lines}
          onChange={(e) => setLines(parseInt(e.target.value, 10) || 100)}
          inputProps={{ min: 10, max: 10000 }}
          sx={{ width: 100 }}
        />
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Time Range</InputLabel>
          <Select
            value={sinceMinutes || ''}
            label="Time Range"
            onChange={(e) => setSinceMinutes(e.target.value ? Number(e.target.value) : undefined)}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value={15}>Last 15 minutes</MenuItem>
            <MenuItem value={30}>Last 30 minutes</MenuItem>
            <MenuItem value={60}>Last hour</MenuItem>
            <MenuItem value={240}>Last 4 hours</MenuItem>
            <MenuItem value={1440}>Last 24 hours</MenuItem>
          </Select>
        </FormControl>
        <TextField
          size="small"
          label="Search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <Search fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ flexGrow: 1, maxWidth: 300 }}
        />
        <Button
          size="small"
          variant="outlined"
          onClick={fetchLogs}
          disabled={loading}
        >
          Apply Filters
        </Button>
      </Box>

      {/* View Mode Tabs */}
      <Tabs
        value={viewMode}
        onChange={(_, newValue) => setViewMode(newValue)}
        sx={{ mb: 2 }}
      >
        <Tab label="Per Pod" value="per-pod" />
        <Tab label="Aggregated" value="aggregated" />
      </Tabs>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Logs Display */}
      <Box
        ref={logContainerRef}
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          backgroundColor: '#1e1e1e',
          color: '#d4d4d4',
          p: 2,
          borderRadius: 1,
          fontFamily: 'monospace',
          fontSize: '0.875rem',
          lineHeight: 1.5,
          maxHeight: '600px',
        }}
      >
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress size={24} />
          </Box>
        ) : viewMode === 'aggregated' ? (
          <Box component="pre" sx={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {aggregatedLogs || 'No logs available'}
          </Box>
        ) : (
          <>
            {filteredLogs && filteredLogs.length > 0 ? (
              filteredLogs.map((pod) => (
                <Box key={pod.pod} sx={{ mb: 3 }}>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <Chip
                      label={pod.pod}
                      size="small"
                      color={pod.ready ? 'success' : 'default'}
                    />
                    {pod.status && (
                      <Chip label={pod.status} size="small" variant="outlined" />
                    )}
                    <Typography variant="caption" color="text.secondary">
                      {pod.lines} lines
                    </Typography>
                  </Box>
                  {pod.error ? (
                    <Alert severity="error" sx={{ mb: 1 }}>
                      {pod.error}
                    </Alert>
                  ) : (
                    <Box
                      component="pre"
                      sx={{
                        margin: 0,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        p: 1,
                        borderRadius: 1,
                      }}
                    >
                      {pod.logs || 'No logs available'}
                    </Box>
                  )}
                </Box>
              ))
            ) : (
              <Typography color="text.secondary">
                {searchTerm ? 'No logs match your search' : 'No logs available'}
              </Typography>
            )}
          </>
        )}
      </Box>

      {/* Summary */}
      {logs && viewMode === 'per-pod' && (
        <Box mt={2} display="flex" gap={2} flexWrap="wrap">
          <Typography variant="caption" color="text.secondary">
            Total Pods: {logs.total_pods}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Total Lines: {logs.total_lines}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Retrieved: {new Date(logs.retrieved_at).toLocaleString()}
          </Typography>
        </Box>
      )}
    </Paper>
  )
}

export default LogViewer

