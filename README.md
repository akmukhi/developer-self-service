# Developer Self-Service Portal

A full-stack web portal where developers can create services, view deployments, request temporary environments, rotate secrets, and check logs/metrics.

## Features

- **Service Management**: Create and manage Kubernetes services
- **Deployment Viewing**: Monitor deployment status and pod health
- **Temporary Environments**: Request and manage isolated environments with TTL
- **Secret Rotation**: Rotate secrets with automatic deployment updates
- **Observability**: View logs and metrics for services

## Tech Stack

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- Material-UI (MUI) for components
- TailwindCSS for styling
- React Router for navigation

### Backend
- FastAPI (Python)
- Kubernetes Python client
- Terraform for infrastructure automation

### Infrastructure
- Kubernetes API integration
- Terraform modules for IaC
- Docker Compose for local development

## Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (minikube, kind, or cloud cluster)
- kubectl configured with cluster access
- Terraform (for infrastructure automation)

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd developer-self-service
   ```

2. **Start services**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **View logs**
   ```bash
   docker-compose logs -f
   ```

5. **Stop services**
   ```bash
   docker-compose down
   ```

### Local Development (Without Docker)

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Kubernetes Setup

The portal requires access to a Kubernetes cluster. For local development, see the detailed guide:

📖 **[Local Kubernetes Setup Guide](docs/LOCAL_K8S_SETUP.md)** - Complete instructions for minikube and kind

### Quick Start

**minikube:**
```bash
minikube start --memory=4096 --cpus=2
minikube addons enable ingress
minikube addons enable metrics-server
```

**kind:**
```bash
kind create cluster --name developer-portal
# See docs/LOCAL_K8S_SETUP.md for ingress and metrics setup
```

### Mounting kubeconfig in Docker

For Docker Compose, you can mount your kubeconfig:

```bash
# Create docker-compose.override.yml
cp docker-compose.override.yml.example docker-compose.override.yml

# Edit and uncomment the kubeconfig mount line
```

Or set the KUBECONFIG environment variable in docker-compose.yml.

## Environment Variables

### Backend
- `LOG_LEVEL`: Logging level (default: INFO)
- `TERRAFORM_BINARY`: Path to terraform binary (default: terraform)
- `KUBECONFIG`: Path to kubeconfig file

### Frontend
- `VITE_API_BASE_URL`: Backend API URL (default: http://localhost:8000/api)

## Project Structure

```
developer-self-service/
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript types
│   └── Dockerfile
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── services/     # Business logic
│   │   └── models/       # Pydantic models
│   └── Dockerfile
├── terraform/            # Terraform modules
│   └── modules/
│       ├── service/      # Service provisioning
│       ├── environment/  # Environment provisioning
│       └── secrets/      # Secret management
├── k8s/                  # Kubernetes manifests
├── docker-compose.yml    # Docker Compose configuration
└── README.md
```

## API Endpoints

### Services
- `POST /api/services` - Create service
- `GET /api/services` - List services
- `GET /api/services/{id}` - Get service details

### Deployments
- `GET /api/deployments` - List deployments
- `GET /api/deployments/{id}` - Get deployment details

### Environments
- `POST /api/environments` - Create temporary environment
- `GET /api/environments` - List environments
- `DELETE /api/environments/{id}` - Delete environment

### Secrets
- `POST /api/secrets/{service_id}/rotate` - Rotate secrets
- `GET /api/secrets/{service_id}` - Get secret info
- `GET /api/secrets/{service_id}/history` - Get rotation history

### Observability
- `GET /api/logs/{service_id}` - Get logs
- `GET /api/metrics/{service_id}` - Get metrics
- `GET /api/logs/{service_id}/statistics` - Get log statistics

## Development

### Hot Reload

Both frontend and backend support hot reload when running with Docker Compose:
- Frontend: Vite dev server with HMR
- Backend: Uvicorn with --reload flag

### Building for Production

```bash
# Build frontend
cd frontend
npm run build

# Build backend
cd backend
docker build -t developer-self-service-backend .
```

## Troubleshooting

### Backend can't connect to Kubernetes

1. Verify kubectl is configured: `kubectl cluster-info`
2. Check kubeconfig is mounted in Docker
3. Verify Kubernetes service account permissions

### Metrics not available

Ensure metrics-server is installed in your cluster:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Terraform not found

Install Terraform and ensure it's in PATH or set `TERRAFORM_BINARY` environment variable.

## License

See LICENSE file for details.
