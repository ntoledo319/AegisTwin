# HydraMind API Documentation

This directory contains the complete API documentation for HydraMind v1.

## 📋 Available Documentation

| File | Purpose | Format |
|------|---------|---------|
| [openapi.yaml](openapi.yaml) | Complete OpenAPI 3.0 specification | YAML |
| README.md | This overview and usage guide | Markdown |

## 🚀 Quick Start

### Using curl

```bash
# Check system health
curl http://localhost:8765/health

# Get system metrics
curl http://localhost:8765/metrics

# List all modules
curl http://localhost:8765/modules

# Publish a test event
curl -X POST http://localhost:8765/bus/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "sensor/temperature",
    "data": {"value": 23.5, "unit": "C"}
  }'

# Query event history
curl -X POST http://localhost:8765/events/query \
  -H "Content-Type: application/json" \
  -d '{
    "topic_pattern": "sensor/*",
    "limit": 10
  }'
```

### Using Python

```python
import requests

# Basic health check
response = requests.get('http://localhost:8765/health')
health = response.json()
print(f"System status: {health['status']}")

# Get metrics
response = requests.get('http://localhost:8765/metrics')
metrics = response.json()
print(f"Events processed: {metrics['eventbus']['messages_processed']}")

# Publish event
event_data = {
    "topic": "sensor/temperature",
    "data": {"value": 25.0, "unit": "C", "sensor_id": "living_room"}
}
response = requests.post('http://localhost:8765/bus/publish', json=event_data)
result = response.json()
print(f"Event published: {result['success']}")
```

## 📚 API Reference

### Endpoints Overview

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|---------------|
| `/` | GET | API information and status | None |
| `/health` | GET | System health check | None |
| `/metrics` | GET | Performance metrics | None |
| `/modules` | GET | List registered modules | None |
| `/config` | GET | Current configuration | None |
| `/bus/publish` | POST | Publish events | None |
| `/events/query` | POST | Query event history | None |
| `/shutdown` | POST | Graceful shutdown | None |

### Response Formats

All endpoints return JSON responses with appropriate HTTP status codes.

**Success Response:**
```json
{
  "status": "healthy",
  "modules": 8,
  "uptime": "2h 15m",
  "health_score": 0.95
}
```

**Error Response:**
```json
{
  "error": "Module not found",
  "code": "MODULE_NOT_FOUND",
  "details": {
    "module_name": "nonexistent_module"
  },
  "timestamp": 1640995200.0
}
```

## 🔧 Advanced Usage

### Event Injection for Testing

```python
import requests

# Inject sensor data
sensor_data = {
    "topic": "sensor/temperature",
    "data": {
        "value": 24.5,
        "unit": "C",
        "sensor_id": "kitchen_thermometer",
        "accuracy": 0.1
    },
    "qos": 1,
    "key": "temp_sensor_001"
}

response = requests.post('http://localhost:8765/bus/publish', json=sensor_data)
if response.status_code == 200:
    print("Event injected successfully")
else:
    print(f"Failed to inject event: {response.text}")
```

### Batch Event Querying

```python
import requests

# Query recent events
query = {
    "topic_pattern": "hvac/*",
    "limit": 50,
    "since": 1640995200,  # Unix timestamp
    "order": "desc"
}

response = requests.post('http://localhost:8765/events/query', json=query)
events = response.json()

print(f"Found {events['total']} events")
for event in events['events'][:5]:
    print(f"- {event['topic']}: {event['data']}")
```

### Monitoring Integration

```python
import requests
import time

def monitor_system():
    while True:
        try:
            # Get health status
            health = requests.get('http://localhost:8765/health').json()

            # Get metrics
            metrics = requests.get('http://localhost:8765/metrics').json()

            # Check for issues
            if health['status'] != 'healthy':
                print(f"⚠️ System health issue: {health['status']}")

            if metrics['eventbus']['dispatch_errors'] > 0:
                print(f"⚠️ Event dispatch errors: {metrics['eventbus']['dispatch_errors']}")

            time.sleep(30)  # Check every 30 seconds

        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(60)

# Run monitoring
monitor_system()
```

## 📊 Metrics and Monitoring

### Available Metrics

#### System Metrics
- **uptime** - System uptime in seconds
- **cpu_usage** - Current CPU utilization percentage
- **memory_usage** - Memory usage in bytes
- **disk_usage** - Disk usage percentage

#### EventBus Metrics
- **messages_published** - Total events published
- **messages_dispatched** - Total events delivered
- **dispatch_errors** - Failed event deliveries
- **queue_size** - Current event queue size
- **subscribers** - Number of active subscribers
- **patterns** - Number of subscription patterns

#### Module Metrics
- **messages_processed** - Events processed by module
- **processing_time_avg** - Average processing time per event
- **errors** - Error count for module
- **memory_usage** - Module memory usage

### Health Monitoring

The health endpoint provides real-time system status:

```json
{
  "status": "healthy",           // "healthy", "degraded", "unhealthy"
  "modules": 8,                 // Number of active modules
  "uptime": "2h 15m 30s",       // Human-readable uptime
  "health_score": 0.95,         // Overall health score (0.0-1.0)
  "details": {                  // Per-module health details
    "temperature_monitor": {
      "state": "running",
      "uptime": 7200.0,
      "message_count": 1500,
      "error_count": 0,
      "health_score": 0.98
    }
  }
}
```

## 🔒 Security Considerations

### Current Security Model

**Development/Testing:**
- No authentication required
- All endpoints accessible
- CORS enabled for web development
- Detailed error messages for debugging

**Production Deployment:**
- Implement authentication mechanisms
- Enable rate limiting and access controls
- Use HTTPS with proper certificates
- Redact sensitive information in responses

### Recommended Security Measures

1. **API Gateway** - Use reverse proxy with authentication
2. **Rate Limiting** - Implement at infrastructure level
3. **Access Logging** - Log all API access for audit trails
4. **Input Validation** - Validate all request parameters
5. **CORS Configuration** - Restrict to trusted origins only

## 🐛 Troubleshooting

### Common Issues

**Connection Refused:**
```bash
# Check if HydraMind is running
curl http://localhost:8765/health

# Check process status
ps aux | grep hydramind

# Check logs
tail -f logs/hydramind.log
```

**Rate Limited:**
```bash
# Response indicates rate limiting
HTTP 429 Too Many Requests

# Wait and retry, or implement exponential backoff
```

**Module Not Found:**
```bash
# Check module registration
curl http://localhost:8765/modules

# Verify module is loaded in configuration
# Check hydramind.yaml features section
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Set debug logging
export HYDRAMIND_LOGGING_LEVEL=DEBUG

# Or in configuration
logging:
  level: "DEBUG"
  json: true
```

## 📚 Additional Resources

- **[EVENTS.md](../EVENTS.md)** - Complete event topic documentation
- **[CONFIGURATION.md](../CONFIGURATION.md)** - Configuration options and examples
- **[DEPLOYMENT.md](../DEPLOYMENT.md)** - Production deployment guide
- **[TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** - Common issues and solutions

---

**The HydraMind API provides comprehensive monitoring and control capabilities for intelligent system management.**
