# Kubernetes Manifests

Kubernetes manifests for deploying the Developer Self-Service Portal.

## Files

- `deployments/backend-deployment.yaml` - Backend API deployment
- `deployments/frontend-deployment.yaml` - Frontend application deployment
- `services/backend-service.yaml` - Backend service
- `services/frontend-service.yaml` - Frontend service
- `configmap.yaml` - Configuration values
- `rbac.yaml` - Service account and RBAC permissions
- `ingress.yaml` - Ingress for external access
- `kustomization.yaml` - Kustomize configuration

## Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Images built and available in registry
- (Optional) Ingress controller (nginx-ingress)

## Deployment

### Using kubectl

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply individually
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress.yaml
```

### Using Kustomize

```bash
kubectl apply -k k8s/
```

### Verify Deployment

```bash
# Check deployments
kubectl get deployments -l managed-by=developer-self-service

# Check services
kubectl get services -l managed-by=developer-self-service

# Check pods
kubectl get pods -l managed-by=developer-self-service

# Check logs
kubectl logs -l app=developer-self-service-backend
kubectl logs -l app=developer-self-service-frontend
```

## Configuration

### ConfigMap

Edit `configmap.yaml` to customize:
- `log_level`: Backend logging level (INFO, DEBUG, etc.)
- `terraform_binary`: Path to terraform binary
- `api_base_url`: Backend API URL for frontend

### Image Configuration

Update the image names in deployment files:
- Backend: `developer-self-service-backend:latest`
- Frontend: `developer-self-service-frontend:latest`

Or use image pull secrets if using private registry.

### Kubeconfig

The backend needs access to the Kubernetes API. Options:

1. **Service Account (Recommended)**: Uses RBAC defined in `rbac.yaml`
2. **Kubeconfig Secret**: Create a secret with kubeconfig:
   ```bash
   kubectl create secret generic kubeconfig-secret \
     --from-file=config=$HOME/.kube/config
   ```

### Ingress

The ingress is configured for nginx-ingress. To use:

1. Install nginx-ingress controller:
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
   ```

2. Update the host in `ingress.yaml` or use a LoadBalancer service

3. For local development with minikube:
   ```bash
   minikube addons enable ingress
   ```

## Resource Requirements

### Backend
- Requests: 200m CPU, 256Mi memory
- Limits: 1000m CPU, 1Gi memory
- Replicas: 2

### Frontend
- Requests: 100m CPU, 128Mi memory
- Limits: 500m CPU, 512Mi memory
- Replicas: 2

## Scaling

To scale deployments:

```bash
kubectl scale deployment developer-self-service-backend --replicas=3
kubectl scale deployment developer-self-service-frontend --replicas=3
```

## Troubleshooting

### Backend can't connect to Kubernetes

1. Check service account:
   ```bash
   kubectl get serviceaccount developer-self-service-backend
   ```

2. Check RBAC:
   ```bash
   kubectl get role,rolebinding -l managed-by=developer-self-service
   ```

3. Check pod logs:
   ```bash
   kubectl logs -l app=developer-self-service-backend
   ```

### Frontend can't reach backend

1. Check services:
   ```bash
   kubectl get svc developer-self-service-backend
   ```

2. Check ConfigMap for correct API URL:
   ```bash
   kubectl get configmap developer-self-service-config -o yaml
   ```

3. Test connectivity from frontend pod:
   ```bash
   kubectl exec -it <frontend-pod> -- wget -O- http://developer-self-service-backend:8000/health
   ```

## Production Considerations

1. **Image Tags**: Use specific version tags instead of `latest`
2. **Resource Limits**: Adjust based on actual usage
3. **Replicas**: Scale based on load
4. **TLS**: Enable TLS in ingress for production
5. **Secrets**: Use Kubernetes secrets for sensitive data
6. **Monitoring**: Add Prometheus annotations for monitoring
7. **Backup**: Consider persistent volumes for Terraform state

