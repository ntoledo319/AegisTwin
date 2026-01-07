# AegisTwin Helm Chart

Kubernetes deployment for AegisTwin - Event-driven agent runtime with governance and deterministic replay.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+

## Installation

### Add the repo (if published)

```bash
helm repo add aegistwin https://charts.aegistwin.io
helm repo update
```

### Install from local chart

```bash
# From the docker/helm directory
helm install aegistwin ./aegistwin

# With custom values
helm install aegistwin ./aegistwin -f my-values.yaml

# In a specific namespace
helm install aegistwin ./aegistwin -n aegistwin --create-namespace
```

## Configuration

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `aegistwin` |
| `image.tag` | Image tag | `latest` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8000` |
| `ingress.enabled` | Enable ingress | `false` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |

### AegisTwin Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `config.runsDir` | Directory for run artifacts | `/app/runs` |
| `config.logLevel` | Log level | `INFO` |
| `config.enableReplay` | Enable replay functionality | `true` |
| `config.enableAudit` | Enable audit logging | `true` |
| `config.policyMode` | Policy enforcement mode | `enforce` |

### Observability

| Parameter | Description | Default |
|-----------|-------------|---------|
| `observability.tracing.enabled` | Enable OpenTelemetry tracing | `false` |
| `observability.tracing.otlpEndpoint` | OTLP endpoint URL | `""` |
| `observability.metrics.enabled` | Enable Prometheus metrics | `true` |

### Persistence

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistent storage | `false` |
| `persistence.storageClass` | Storage class | `""` |
| `persistence.size` | Volume size | `1Gi` |

## Examples

### Basic Installation

```bash
helm install aegistwin ./aegistwin
```

### With Ingress

```bash
helm install aegistwin ./aegistwin \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=aegistwin.example.com \
  --set ingress.hosts[0].paths[0].path=/ \
  --set ingress.hosts[0].paths[0].pathType=Prefix
```

### With Tracing

```bash
helm install aegistwin ./aegistwin \
  --set observability.tracing.enabled=true \
  --set observability.tracing.otlpEndpoint=http://jaeger:4317
```

### Production Configuration

```yaml
# production-values.yaml
replicaCount: 3

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

persistence:
  enabled: true
  storageClass: gp2
  size: 10Gi

observability:
  tracing:
    enabled: true
    otlpEndpoint: http://jaeger.monitoring:4317
```

```bash
helm install aegistwin ./aegistwin -f production-values.yaml
```

## Upgrading

```bash
helm upgrade aegistwin ./aegistwin
```

## Uninstalling

```bash
helm uninstall aegistwin
```

## Troubleshooting

### Check pod status

```bash
kubectl get pods -l app.kubernetes.io/name=aegistwin
```

### View logs

```bash
kubectl logs -l app.kubernetes.io/name=aegistwin
```

### Port forward for testing

```bash
kubectl port-forward svc/aegistwin 8000:8000
curl http://localhost:8000/health
```

---

*Last updated: 2026-01-07*
