# Developer Self-Service Portal

A full-stack web portal that empowers developers to self-manage their Kubernetes services, deployments, environments, secrets, and observability without requiring deep Kubernetes expertise.

## Features

- **Service Management**: Create and manage Kubernetes services with custom resource requirements
- **Deployment Monitoring**: Real-time view of deployment status, pod health, and replica counts
- **Temporary Environments**: Request isolated Kubernetes namespaces with automatic TTL-based cleanup
- **Secret Rotation**: Rotate secrets securely with automatic deployment rolling updates
- **Observability**: View aggregated logs, metrics (CPU/memory), and log statistics for services

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  - Material-UI Components                                    │
│  - TypeScript with Type Safety                              │
│  - React Router for Navigation                              │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────▼──────────────────────────────────────┐
│                  Backend (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Kubernetes   │  │  Terraform   │  │   Secrets    │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Logging    │  │   Metrics    │                        │
│  │   Service    │  │   Service    │                        │
│  └──────────────┘  └──────────────┘                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐
│ Kubernetes   │ │ Terraform  │ │  Secrets  │
│     API      │ │  Binary    │ │    API    │
└──────────────┘ └────────────┘ └───────────┘
```

### Component Details

**Frontend Layer:**
- React 18 with TypeScript for type safety
- Material-UI for consistent UI components
- TailwindCSS for custom styling
- Axios for API communication
- React Router for client-side routing

**Backend Layer:**
- FastAPI for high-performance async API
- Pydantic models for request/response validation
- Modular service architecture:
  - `kubernetes_service`: Kubernetes API client wrapper
  - `terraform_service`: Terraform execution and state management
  - `secrets_service`: Secret generation and rotation logic
  - `logging_service`: Log aggregation and filtering
  - `metrics_service`: Metrics API integration

**Infrastructure Layer:**
- Kubernetes API for resource management
- Terraform modules for Infrastructure as Code
- Kubernetes Secrets API for secret management
- Metrics Server for resource metrics

### Data Flow

1. **Service Creation:**
   - User submits service configuration → Backend validates → Terraform provisions → Kubernetes creates resources → Secrets generated → Status returned

2. **Secret Rotation:**
   - User requests rotation → New secret generated → Kubernetes Secret updated → Deployment rolling update triggered → History logged

3. **Observability:**
   - User requests logs/metrics → Backend queries Kubernetes API → Logs aggregated/filtered → Metrics parsed → Response formatted → Frontend displays

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast build tooling and HMR
- **Material-UI (MUI)** for component library
- **TailwindCSS** for utility-first styling
- **React Router** for navigation
- **Axios** for HTTP client

### Backend
- **FastAPI** (Python 3.11+) for async API
- **Uvicorn** as ASGI server
- **Pydantic** for data validation
- **kubernetes** Python client library
- **Terraform** for infrastructure automation

### Infrastructure
- **Kubernetes** (1.20+) for orchestration
- **Docker** and **Docker Compose** for containerization
- **Terraform** modules for IaC
- **Nginx** for frontend serving (production)

## Prerequisites

### Required
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Kubernetes cluster** (minikube, kind, or cloud cluster)
- **kubectl** configured with cluster access
- **Terraform** 1.0+ (for infrastructure automation)

### Optional
- **Node.js** 18+ and **npm** (for local frontend development)
- **Python** 3.11+ (for local backend development)

## Setup Instructions

### 1. Clone Repository

```bash
git clone <repository-url>
cd developer-self-service
```

### 2. Kubernetes Cluster Setup

The portal requires access to a Kubernetes cluster. Choose one option:

#### Option A: Local Development (Recommended)

📖 **[Complete Local Kubernetes Setup Guide](docs/LOCAL_K8S_SETUP.md)**

**Quick Start with minikube:**
```bash
minikube start --memory=4096 --cpus=2
minikube addons enable ingress
minikube addons enable metrics-server
```

**Quick Start with kind:**
```bash
kind create cluster --name developer-portal
# See docs/LOCAL_K8S_SETUP.md for complete setup
```

#### Option B: Existing Cluster

Ensure you have:
- `kubectl` configured: `kubectl cluster-info`
- Metrics Server installed (for metrics functionality)
- Ingress Controller (optional, for external access)

### 3. Configure Kubernetes Access

#### For Docker Compose

Create `docker-compose.override.yml`:
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

Edit and uncomment the kubeconfig mount:
```yaml
services:
  backend:
    volumes:
      - ${HOME}/.kube:/app/.kube:ro
```

#### For Kubernetes Deployment

The backend uses a ServiceAccount with RBAC permissions (see `k8s/rbac.yaml`). No additional configuration needed.

### 4. Start the Application

#### Using Docker Compose (Recommended for Development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access Points:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Interactive API: http://localhost:8000/redoc

#### Local Development (Without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export KUBECONFIG=$HOME/.kube/config
export LOG_LEVEL=DEBUG

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install

# Set API URL (optional, defaults to http://localhost:8000/api)
export VITE_API_BASE_URL=http://localhost:8000/api

# Run development server
npm run dev
```

### 5. Deploy to Kubernetes (Production)

#### Build Images

```bash
# Build backend
cd backend
docker build -t developer-self-service-backend:latest .

# Build frontend
cd ../frontend
docker build -t developer-self-service-frontend:latest .
```

#### Load Images (for local clusters)

**minikube:**
```bash
eval $(minikube docker-env)
docker build -t developer-self-service-backend:latest ./backend
docker build -t developer-self-service-frontend:latest ./frontend
eval $(minikube docker-env -u)
```

**kind:**
```bash
kind load docker-image developer-self-service-backend:latest --name developer-portal
kind load docker-image developer-self-service-frontend:latest --name developer-portal
```

#### Apply Kubernetes Manifests

```bash
# Apply all resources
kubectl apply -k k8s/

# Or apply individually
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress.yaml
```

#### Verify Deployment

```bash
# Check pods
kubectl get pods -l managed-by=developer-self-service

# Check services
kubectl get svc -l managed-by=developer-self-service

# View logs
kubectl logs -l app=developer-self-service-backend -f
```

See [k8s/README.md](k8s/README.md) for detailed deployment instructions.

## Usage Guide

### Service Management

#### Create a Service

1. Navigate to **Services** page
2. Click **Create Service** button
3. Fill in the form:
   - **Name**: Unique service identifier
   - **Image**: Container image (e.g., `nginx:latest`)
   - **Replicas**: Number of pod replicas
   - **Resources**: CPU and memory requests/limits
   - **Environment Variables**: Key-value pairs
   - **Ports**: Container and service ports
4. Click **Create**

The backend will:
- Create Kubernetes Deployment
- Create Kubernetes Service
- Generate and attach secrets
- Return service status

#### View Services

- **Services Page**: Lists all services with status, replicas, and resource info
- **Filter**: By status (Active, Pending, Failed)
- **Search**: By service name
- **Details**: Click on a service card for detailed information

#### Service Status

- **Active**: Service is running with all pods healthy
- **Pending**: Service is being created or updated
- **Failed**: Service creation failed or pods are unhealthy

### Deployment Monitoring

#### View Deployments

1. Navigate to **Deployments** page
2. View all Kubernetes deployments
3. Filter by status or search by name

#### Deployment Details

Each deployment card shows:
- **Status**: Current deployment state
- **Replicas**: Desired vs. available replicas
- **Image**: Container image version
- **Pods**: Individual pod status
- **Age**: Time since creation

### Temporary Environments

#### Create Environment

1. Navigate to **Environments** page
2. Click **Request Environment**
3. Configure:
   - **Name**: Environment identifier
   - **TTL**: Time-to-live in hours
   - **Services**: Services to deploy in the environment
   - **Labels**: Optional metadata
4. Click **Create**

The system will:
- Create a Kubernetes namespace
- Set up resource quotas and limits
- Deploy requested services
- Schedule automatic cleanup

#### Manage Environments

- **List**: View all environments with TTL countdown
- **Delete**: Manually delete before TTL expires
- **Status**: Active, Expiring, Expired

### Secret Management

#### Rotate Secrets

1. Navigate to **Secrets** page
2. Find the service secret
3. Click **Rotate Secret**
4. Select:
   - **Keys to Rotate**: Specific secret keys or all
   - **Update Deployments**: Trigger rolling update
5. Click **Rotate**

The system will:
- Generate new secret values
- Update Kubernetes Secret
- Optionally trigger deployment rolling update
- Log rotation history

#### View Secret History

- Click on a secret card to expand
- View rotation history with timestamps
- See which keys were rotated

### Observability

#### View Logs

1. Navigate to **Observability** page
2. Select a service
3. Choose log view:
   - **Per-Pod**: Individual pod logs
   - **Aggregated**: Combined logs from all pods
4. Apply filters:
   - **Lines**: Limit number of lines
   - **Time**: Filter by time range
   - **Search**: Search for specific terms
5. **Auto-refresh**: Enable for real-time updates
6. **Download**: Export logs as text file

#### View Metrics

1. Navigate to **Observability** page
2. Select **Metrics** tab
3. View:
   - **Summary**: Overall CPU/memory usage
   - **Detailed**: Per-pod metrics
4. **Auto-refresh**: Update metrics automatically

**Note**: Metrics require metrics-server installed in your cluster.

#### Log Statistics

View aggregated statistics:
- Total log lines
- Error count
- Warning count
- Most common log levels

## API Reference

### Base URL

- Local: `http://localhost:8000/api`
- Kubernetes: `http://developer-self-service-backend:8000/api`

### Authentication

Currently, the API does not require authentication. For production, implement authentication middleware.

### Endpoints

#### Services

```http
POST   /api/services              # Create service
GET    /api/services              # List services
GET    /api/services/{id}         # Get service details
```

#### Deployments

```http
GET    /api/deployments           # List deployments
GET    /api/deployments/{id}      # Get deployment details
```

#### Environments

```http
POST   /api/environments         # Create environment
GET    /api/environments         # List environments
GET    /api/environments/{id}    # Get environment details
DELETE /api/environments/{id}    # Delete environment
```

#### Secrets

```http
POST   /api/secrets/{service_id}/rotate    # Rotate secrets
GET    /api/secrets/{service_id}           # Get secret info
GET    /api/secrets                        # List all secrets
GET    /api/secrets/{service_id}/history   # Get rotation history
```

#### Observability

```http
GET    /api/logs/{service_id}                    # Get pod logs
GET    /api/logs/{service_id}/aggregated         # Get aggregated logs
GET    /api/logs/{service_id}/statistics         # Get log statistics
GET    /api/deployments/{deployment_id}/logs     # Get deployment logs
GET    /api/metrics/{service_id}                 # Get service metrics
GET    /api/metrics/{service_id}/summary         # Get metrics summary
GET    /api/deployments/{deployment_id}/metrics  # Get deployment metrics
GET    /api/metrics/availability                 # Check metrics availability
```

#### Health

```http
GET    /health                   # Health check
```

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `TERRAFORM_BINARY` | Path to terraform binary | `terraform` |
| `KUBECONFIG` | Path to kubeconfig file | `/app/.kube/config` or in-cluster config |
| `PYTHONUNBUFFERED` | Disable Python output buffering | `1` |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api` |

## Project Structure

```
developer-self-service/
├── frontend/                    # React frontend application
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── Layout.tsx       # Main layout with navigation
│   │   │   ├── ServiceForm.tsx  # Service creation form
│   │   │   ├── ServiceCard.tsx  # Service display card
│   │   │   ├── DeploymentCard.tsx
│   │   │   ├── EnvironmentRequest.tsx
│   │   │   ├── EnvironmentCard.tsx
│   │   │   ├── SecretRotator.tsx
│   │   │   ├── SecretCard.tsx
│   │   │   ├── LogViewer.tsx
│   │   │   └── MetricsChart.tsx
│   │   ├── pages/               # Page components
│   │   │   ├── HomePage.tsx
│   │   │   ├── ServicesPage.tsx
│   │   │   ├── DeploymentsPage.tsx
│   │   │   ├── EnvironmentsPage.tsx
│   │   │   ├── SecretsPage.tsx
│   │   │   └── ObservabilityPage.tsx
│   │   ├── services/
│   │   │   └── api.ts           # API client with Axios
│   │   ├── types/
│   │   │   └── index.ts         # TypeScript type definitions
│   │   ├── App.tsx              # Main app component
│   │   └── main.tsx             # Entry point
│   ├── Dockerfile               # Production build
│   ├── Dockerfile.dev           # Development build
│   └── nginx.conf               # Nginx configuration
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/                 # API endpoints
│   │   │   ├── services.py      # Service management endpoints
│   │   │   ├── deployments.py  # Deployment endpoints
│   │   │   ├── environments.py # Environment endpoints
│   │   │   ├── secrets.py      # Secret endpoints
│   │   │   └── observability.py # Logs/metrics endpoints
│   │   ├── services/            # Business logic
│   │   │   ├── kubernetes_service.py  # K8s API client
│   │   │   ├── terraform_service.py   # Terraform execution
│   │   │   ├── secrets_service.py     # Secret management
│   │   │   ├── logging_service.py     # Log aggregation
│   │   │   └── metrics_service.py     # Metrics retrieval
│   │   ├── models/              # Pydantic models
│   │   │   ├── service.py
│   │   │   ├── deployment.py
│   │   │   ├── environment.py
│   │   │   └── secret.py
│   │   └── main.py              # FastAPI app initialization
│   ├── Dockerfile               # Production build
│   ├── Dockerfile.dev           # Development build
│   └── requirements.txt         # Python dependencies
├── terraform/                   # Terraform modules
│   └── modules/
│       ├── service/             # Service provisioning module
│       ├── environment/         # Environment provisioning module
│       └── secrets/             # Secret management module
├── k8s/                         # Kubernetes manifests
│   ├── deployments/             # Deployment manifests
│   ├── services/                # Service manifests
│   ├── configmap.yaml          # Configuration
│   ├── rbac.yaml                # RBAC permissions
│   ├── ingress.yaml             # Ingress configuration
│   └── README.md                # K8s deployment guide
├── docs/                        # Documentation
│   └── LOCAL_K8S_SETUP.md      # Local K8s setup guide
├── docker-compose.yml           # Docker Compose configuration
├── docker-compose.override.yml.example  # Override example
└── README.md                    # This file
```

## Development

### Hot Reload

Both frontend and backend support hot reload when running with Docker Compose:
- **Frontend**: Vite dev server with HMR (Hot Module Replacement)
- **Backend**: Uvicorn with `--reload` flag

### Building for Production

#### Frontend

```bash
cd frontend
npm run build
# Output in dist/
```

#### Backend

```bash
cd backend
docker build -t developer-self-service-backend:latest .
```

### Running Tests

```bash
# Backend tests (when implemented)
cd backend
pytest

# Frontend tests (when implemented)
cd frontend
npm test
```

### Code Quality

```bash
# Backend linting
cd backend
flake8 app/
black app/ --check
mypy app/

# Frontend linting
cd frontend
npm run lint
```

## Troubleshooting

### Backend Can't Connect to Kubernetes

**Symptoms**: Errors about Kubernetes API connection

**Solutions**:
1. Verify kubectl is configured: `kubectl cluster-info`
2. Check kubeconfig is mounted in Docker (if using Docker Compose)
3. Verify Kubernetes service account permissions: `kubectl get role,rolebinding -l managed-by=developer-self-service`
4. Check pod logs: `kubectl logs -l app=developer-self-service-backend`

### Metrics Not Available

**Symptoms**: Metrics endpoints return errors or empty data

**Solutions**:
1. Ensure metrics-server is installed:
   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
   ```
2. For kind, patch metrics-server:
   ```bash
   kubectl patch deployment metrics-server -n kube-system --type='json' \
     -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
   ```
3. Verify metrics-server is running: `kubectl get pods -n kube-system | grep metrics-server`

### Terraform Not Found

**Symptoms**: Service creation fails with "terraform not found"

**Solutions**:
1. Install Terraform: https://www.terraform.io/downloads
2. Ensure Terraform is in PATH: `which terraform`
3. Set `TERRAFORM_BINARY` environment variable to full path
4. For Docker, ensure Terraform is installed in the image

### Frontend Can't Reach Backend

**Symptoms**: API calls fail with connection errors

**Solutions**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `VITE_API_BASE_URL` environment variable
3. For Docker Compose, ensure services are on the same network
4. Check browser console for CORS errors (backend CORS should be configured)

### Pods Not Starting

**Symptoms**: Pods stuck in Pending or CrashLoopBackOff

**Solutions**:
1. Check pod status: `kubectl describe pod <pod-name>`
2. Check events: `kubectl get events --sort-by='.lastTimestamp'`
3. Verify image exists: `docker images | grep developer-self-service`
4. Check resource constraints: `kubectl top nodes`
5. Review pod logs: `kubectl logs <pod-name>`

### Ingress Not Working

**Symptoms**: Can't access portal via ingress URL

**Solutions**:
1. Verify ingress controller is installed:
   ```bash
   kubectl get pods -n ingress-nginx
   ```
2. For minikube: `minikube addons enable ingress`
3. Check ingress status: `kubectl describe ingress developer-self-service-ingress`
4. Verify ingress class: `kubectl get ingressclass`
5. Check ingress controller logs

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

## Security Considerations

- **Authentication**: Currently not implemented. Add authentication middleware for production.
- **RBAC**: Backend uses minimal required permissions. Review `k8s/rbac.yaml`.
- **Secrets**: Never expose secret values in API responses. Only metadata is returned.
- **Network**: Use TLS/HTTPS in production. Configure ingress with TLS certificates.
- **Image Security**: Use specific image tags, not `latest`. Scan images for vulnerabilities.

## Roadmap

- [ ] Authentication and authorization (OAuth2, JWT)
- [ ] Multi-cluster support
- [ ] Service templates and presets
- [ ] Advanced log filtering and search
- [ ] Metrics dashboards and alerts
- [ ] Cost tracking and resource optimization
- [ ] CI/CD integration
- [ ] Audit logging
- [ ] Webhook notifications

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in `docs/`
- Review API documentation at `/docs` endpoint
