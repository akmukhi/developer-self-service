# Local Kubernetes Cluster Setup Guide

This guide covers setting up a local Kubernetes cluster for developing and testing the Developer Self-Service Portal.

## Prerequisites

- Docker Desktop installed and running
- kubectl installed
- At least 4GB RAM available for the cluster
- At least 2 CPU cores available

## Option 1: minikube

### Installation

**macOS:**
```bash
brew install minikube
```

**Linux:**
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

**Windows:**
```bash
# Using Chocolatey
choco install minikube

# Or download from: https://minikube.sigs.k8s.io/docs/start/
```

### Starting minikube

```bash
# Start minikube with recommended settings
minikube start --memory=4096 --cpus=2

# Or with more resources for better performance
minikube start --memory=8192 --cpus=4

# Verify cluster is running
minikube status
kubectl cluster-info
```

### Configure kubectl

```bash
# minikube automatically configures kubectl
kubectl config current-context
# Should show: minikube

# Verify connection
kubectl get nodes
```

### Enable Addons

```bash
# Enable ingress controller (for external access)
minikube addons enable ingress

# Enable metrics-server (for metrics API)
minikube addons enable metrics-server

# List all addons
minikube addons list
```

### Accessing Services

```bash
# Get minikube IP
minikube ip

# Access services via minikube service
minikube service developer-self-service-frontend

# Or use port-forward
kubectl port-forward service/developer-self-service-frontend 8080:80
```

### Stopping and Deleting

```bash
# Stop minikube (keeps cluster data)
minikube stop

# Delete cluster
minikube delete

# Start again
minikube start
```

## Option 2: kind (Kubernetes in Docker)

### Installation

**macOS:**
```bash
brew install kind
```

**Linux/Windows:**
```bash
# Download binary
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### Creating a Cluster

```bash
# Create a basic cluster
kind create cluster --name developer-portal

# Create cluster with custom configuration
cat <<EOF | kind create cluster --name developer-portal --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
EOF
```

### Configure kubectl

```bash
# kind automatically configures kubectl
kubectl cluster-info --context kind-developer-portal

# Verify connection
kubectl get nodes
```

### Install Ingress Controller

```bash
# Install nginx ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### Install Metrics Server

```bash
# Install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch for kind (disable TLS verification)
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

# Verify metrics-server is running
kubectl get pods -n kube-system | grep metrics-server
```

### Accessing Services

```bash
# List clusters
kind get clusters

# Get kubeconfig
kind get kubeconfig --name developer-portal

# Delete cluster
kind delete cluster --name developer-portal
```

## Setting Up the Portal

### 1. Build and Load Images

**For minikube:**
```bash
# Set Docker environment to minikube
eval $(minikube docker-env)

# Build images
cd backend
docker build -t developer-self-service-backend:latest .
cd ../frontend
docker build -t developer-self-service-frontend:latest .

# Reset Docker environment
eval $(minikube docker-env -u)
```

**For kind:**
```bash
# Build images
cd backend
docker build -t developer-self-service-backend:latest .
cd ../frontend
docker build -t developer-self-service-frontend:latest .

# Load images into kind
kind load docker-image developer-self-service-backend:latest --name developer-portal
kind load docker-image developer-self-service-frontend:latest --name developer-portal
```

### 2. Update Image Pull Policy

Edit the deployment files to use `IfNotPresent` or `Never`:

```yaml
# In k8s/deployments/backend-deployment.yaml and frontend-deployment.yaml
imagePullPolicy: IfNotPresent  # or Never for local images
```

### 3. Deploy the Portal

```bash
# Apply all manifests
kubectl apply -k k8s/

# Or apply individually
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress.yaml
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -l managed-by=developer-self-service

# Check services
kubectl get svc -l managed-by=developer-self-service

# Check ingress
kubectl get ingress

# View logs
kubectl logs -l app=developer-self-service-backend -f
kubectl logs -l app=developer-self-service-frontend -f
```

### 5. Access the Portal

**With Ingress (minikube):**
```bash
# Get minikube IP
MINIKUBE_IP=$(minikube ip)

# Add to /etc/hosts (or C:\Windows\System32\drivers\etc\hosts on Windows)
echo "$MINIKUBE_IP developer-portal.local" | sudo tee -a /etc/hosts

# Access at http://developer-portal.local
```

**With Ingress (kind):**
```bash
# Access at http://localhost (if configured with port mappings)
# Or use port-forward
kubectl port-forward service/developer-self-service-frontend 8080:80
# Access at http://localhost:8080
```

**With Port Forwarding:**
```bash
# Frontend
kubectl port-forward service/developer-self-service-frontend 8080:80

# Backend
kubectl port-forward service/developer-self-service-backend 8000:8000

# Access frontend at http://localhost:8080
# API at http://localhost:8000
```

## Configuration

### Update ConfigMap for Local Development

Edit `k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: developer-self-service-config
data:
  log_level: "DEBUG"  # More verbose for local dev
  terraform_binary: "terraform"
  api_base_url: "http://developer-self-service-backend:8000/api"
```

### Service Account Permissions

The RBAC configuration in `k8s/rbac.yaml` provides the backend with necessary permissions. For local development, you might need to adjust based on your cluster's security policies.

### Kubeconfig Access

The backend needs access to the Kubernetes API. Options:

**Option 1: Service Account (Recommended)**
- Uses the ServiceAccount defined in `rbac.yaml`
- No additional configuration needed

**Option 2: Mount Kubeconfig (For Testing)**
```bash
# Create secret from local kubeconfig
kubectl create secret generic kubeconfig-secret \
  --from-file=config=$HOME/.kube/config \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -l managed-by=developer-self-service

# Describe pod for events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>
```

### Image Pull Errors

```bash
# Verify images are loaded
docker images | grep developer-self-service

# For minikube, check minikube's Docker
eval $(minikube docker-env)
docker images
eval $(minikube docker-env -u)

# For kind, verify images are loaded
docker exec -it developer-portal-control-plane crictl images | grep developer-self-service
```

### Backend Can't Connect to Kubernetes

```bash
# Check service account
kubectl get serviceaccount developer-self-service-backend

# Check RBAC
kubectl get role,rolebinding -l managed-by=developer-self-service

# Test from backend pod
kubectl exec -it <backend-pod> -- python -c "from kubernetes import config; config.load_incluster_config(); print('OK')"
```

### Metrics Not Available

```bash
# Check if metrics-server is running
kubectl get pods -n kube-system | grep metrics-server

# For kind, ensure TLS verification is disabled
kubectl get deployment metrics-server -n kube-system -o yaml

# Test metrics API
kubectl top nodes
kubectl top pods
```

### Ingress Not Working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress resource
kubectl describe ingress developer-self-service-ingress

# For minikube, ensure ingress addon is enabled
minikube addons list | grep ingress
```

### Resource Constraints

If pods are being evicted or not starting:

```bash
# Check node resources
kubectl top nodes

# Reduce resource requests in deployment files
# Edit k8s/deployments/*.yaml and lower requests/limits
```

## Development Workflow

### 1. Start Cluster

```bash
# minikube
minikube start

# kind
kind create cluster --name developer-portal
```

### 2. Build and Load Images

```bash
# Build images
docker build -t developer-self-service-backend:latest ./backend
docker build -t developer-self-service-frontend:latest ./frontend

# Load into cluster (see instructions above)
```

### 3. Deploy Portal

```bash
kubectl apply -k k8s/
```

### 4. Access Portal

```bash
# Port forward or use ingress (see above)
kubectl port-forward service/developer-self-service-frontend 8080:80
```

### 5. Make Changes

```bash
# Rebuild images
docker build -t developer-self-service-backend:latest ./backend

# Reload into cluster
# Restart deployments
kubectl rollout restart deployment/developer-self-service-backend
```

## Quick Reference

### minikube Commands

```bash
minikube start          # Start cluster
minikube stop           # Stop cluster
minikube delete         # Delete cluster
minikube status         # Check status
minikube ip             # Get cluster IP
minikube service <svc>  # Open service in browser
minikube dashboard      # Open Kubernetes dashboard
minikube addons list    # List addons
minikube addons enable <name>  # Enable addon
```

### kind Commands

```bash
kind create cluster --name <name>  # Create cluster
kind get clusters                  # List clusters
kind delete cluster --name <name>  # Delete cluster
kind load docker-image <image> --name <cluster>  # Load image
kind get kubeconfig --name <name>  # Get kubeconfig
```

### kubectl Commands

```bash
kubectl get pods                    # List pods
kubectl get svc                     # List services
kubectl get ingress                 # List ingress
kubectl logs <pod>                  # View logs
kubectl describe <resource> <name>  # Describe resource
kubectl port-forward <svc> <port>   # Port forward
kubectl exec -it <pod> -- <cmd>     # Execute command in pod
```

## Next Steps

1. Deploy the portal using the manifests in `k8s/`
2. Configure ingress for external access
3. Set up monitoring and logging
4. Configure persistent storage if needed
5. Set up CI/CD for automated deployments

For more information, see the main [README.md](../README.md).

