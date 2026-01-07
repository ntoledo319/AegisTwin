# AegisTwin Observability Stack

Pre-configured observability setup with Prometheus, Grafana, and Jaeger.

## Quick Start

```bash
cd docker
docker-compose up -d
```

Access the services:
- **AegisTwin API**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686

## Components

### Prometheus

Metrics collection and storage.

**Configuration**: `prometheus/prometheus.yml`

Scrapes metrics from:
- AegisTwin API (`/metrics` endpoint)
- Self-monitoring

### Grafana

Visualization and dashboards.

**Dashboards**:
- `grafana/dashboards/aegistwin-overview.json` - Main operational dashboard

**Provisioning**:
- `grafana/provisioning/dashboards.yaml` - Dashboard auto-provisioning
- `grafana/provisioning/datasources.yaml` - Prometheus/Jaeger datasources

### Jaeger

Distributed tracing.

Enable tracing in AegisTwin:
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=aegistwin
```

## Dashboard Overview

The AegisTwin Overview dashboard includes:

| Panel | Description |
|-------|-------------|
| Events per Second | Real-time event throughput by type |
| Event Type Distribution | Pie chart of event types |
| Active Runs | Current number of active pipeline runs |
| Policy Checks | Allow/deny rate over time |
| Query Latency | p50, p95, p99 latency percentiles |
| Replay Success Rate | Percentage of successful replays |
| Total Events | Cumulative event count |
| Service Health | Up/down status |

## Metrics Reference

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `aegistwin_events_total` | Counter | `event_type` | Total events processed |
| `aegistwin_policy_checks_total` | Counter | `outcome` | Policy check results |
| `aegistwin_event_latency_seconds` | Histogram | `operation` | Event processing latency |
| `aegistwin_active_runs` | Gauge | - | Currently active runs |

## Alerts (Optional)

Add alerts to `prometheus/alerts.yml`:

```yaml
groups:
  - name: aegistwin
    rules:
      - alert: HighPolicyDenyRate
        expr: rate(aegistwin_policy_checks_total{outcome="deny"}[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High policy deny rate"

      - alert: ServiceDown
        expr: up{job="aegistwin"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "AegisTwin is down"
```

## Customization

### Adding Panels

1. Open Grafana at http://localhost:3000
2. Navigate to the AegisTwin Overview dashboard
3. Click "Add panel"
4. Configure your visualization
5. Save the dashboard

### Custom Metrics

Add custom metrics in your code:

```python
from aegistwin.observability import record_event, record_latency

# Record custom event
record_event("my_custom_event")

# Record latency
with LatencyTimer("my_operation"):
    do_something()
```

## Troubleshooting

### No Metrics Showing

1. Check AegisTwin is running: `curl http://localhost:8000/health`
2. Check metrics endpoint: `curl http://localhost:8000/metrics`
3. Check Prometheus targets: http://localhost:9090/targets

### Dashboard Empty

1. Verify Prometheus datasource is configured
2. Check time range (top right)
3. Generate some data: `curl -X POST http://localhost:8000/demo/pipeline`

### Tracing Not Working

1. Check Jaeger is running: http://localhost:16686
2. Verify OTEL environment variables
3. Check for errors in application logs

## Production Deployment

For production:

1. **Use persistent storage** for Prometheus and Grafana
2. **Enable authentication** for Grafana
3. **Configure retention** policies
4. **Set up alerts** for critical metrics
5. **Use external Prometheus** for high availability

```yaml
# Example production values
prometheus:
  retention: 30d
  storage: 100Gi
  replicas: 2

grafana:
  persistence:
    enabled: true
    size: 10Gi
  adminPassword: <secure-password>
```

---

*Last updated: 2026-01-07*
