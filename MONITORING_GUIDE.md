# DCIS Monitoring & Performance Testing Guide

## 🚀 Performance Testing

### Load Testing with Locust

Test sustained load of 100 queries/minute:

```bash
cd /Users/dasuncharuka/Documents/projects/llm/dcis/backend

# Start backend first
uvicorn src.api.main:app --reload

# Open new terminal - Web UI mode (recommended)
locust -f tests/performance/locustfile.py --host=http://localhost:8000 --web-port=8089

# Then open: http://localhost:8089
# Set users: 10, spawn rate: 1, duration: 5m

# Or headless mode
locust -f tests/performance/locustfile.py \
       --host=http://localhost:8000 \
       --users 10 --spawn-rate 1 \
       --run-time 5m --headless
```

**Expected Results:**
- P99 latency < 2s
- Error rate < 5%
- 100+ requests/min sustained

### Benchmarking with pytest-benchmark

```bash
# Run all benchmarks
pytest tests/performance/test_benchmarks.py --benchmark-only

# Save baseline
pytest tests/performance/test_benchmarks.py --benchmark-save=baseline

# Compare against baseline
pytest tests/performance/test_benchmarks.py --benchmark-compare=baseline

# View results
pytest tests/performance/test_benchmarks.py --benchmark-histogram
```

### Memory Profiling

```bash
# 30-minute leak test
python scripts/profile_memory.py --duration 1800 --interval 10

# With workload simulation
python scripts/profile_memory.py --duration 1800 --workload

# Check output: memory_profile_*.png
```

**Pass Criteria:**
- Memory growth < 20% over 30 minutes
- No unbounded growth pattern

### 3D Performance Testing

```bash
cd /Users/dasuncharuka/Documents/projects/llm/dcis/frontend

# Run 3D performance tests
npm run test:e2e -- performance-3d.spec.ts

# Or with Playwright UI
npx playwright test --ui performance-3d.spec.ts
```

**Expected Results:**
- Orbit: 55+ FPS average, 45+ FPS minimum
- Cortex (500 nodes): 50+ FPS average
- Frame drops < 20% during interaction
- Memory growth < 50% in 30s

---

## 📊 Observability Stack

### Starting the Monitoring Stack

```bash
cd /Users/dasuncharuka/Documents/projects/llm/dcis/infrastructure/docker

# Start all monitoring services
docker-compose -f monitoring-stack.yml up -d

# Check status
docker-compose -f monitoring-stack.yml ps

# View logs
docker-compose -f monitoring-stack.yml logs -f jaeger
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Jaeger** (Tracing) | http://localhost:16686 | None |
| **Kibana** (Logs) | http://localhost:5601 | None |
| **Grafana** (Metrics) | http://localhost:3001 | admin / dcis2024 |
| **Prometheus** | http://localhost:9090 | None |
| **Alertmanager** | http://localhost:9093 | None |

### Enable Tracing in Backend

```python
# backend/src/api/main.py
from backend.src.core.tracing import setup_tracing

app = FastAPI()

# Enable tracing
setup_tracing(
    app,
    service_name="dcis-backend",
    jaeger_host="localhost",
    jaeger_port=6831,
    enabled=True
)
```

### Using Trace Decorators

```python
from backend.src.core.tracing import trace_agent_task, trace_memory_operation

@trace_agent_task("logician", "reasoning")
async def process_reasoning_task(self, task):
    # Automatically traced
    ...

@trace_memory_operation("store_episodic")
async def store_memory(self, data):
    # Traced with memory.* span
    ...
```

### Viewing Traces in Jaeger

1. Open http://localhost:16686
2. Select Service: `dcis-backend`
3. Click "Find Traces"
4. View request flow across agents

---

## 🔔 Alerting

### Configure Slack Webhook

Edit `infrastructure/docker/alertmanager.yml`:

```yaml
receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#dcis-alerts'
```

### Configure PagerDuty

```yaml
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

### Test Alerts

```bash
# Simulate high error rate
# Make failed requests to trigger HighErrorRate alert

# Check Alertmanager
open http://localhost:9093
```

---

## 📈 Grafana Dashboards

### Import Default Dashboards

1. Login to Grafana: http://localhost:3001
2. Go to Dashboards → Import
3. Import these dashboard IDs:
   - `3662` - Prometheus 2.0 Stats
   - `1860` - Node Exporter Full
   - `7362` - PostgreSQL Database
   - `11159` - FastAPI Dashboard

### Create Custom DCIS Dashboard

```json
{
  "panels": [
    {
      "title": "Query Processing Rate",
      "targets": [{"expr": "rate(http_requests_total{job='dcis-backend'}[5m])"}]
    },
    {
      "title": "P99 Latency",
      "targets": [{"expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))"}]
    }
  ]
}
```

---

## 🧪 Verification Checklist

### Performance

- [ ] Load test: 100 qpm sustained for 5 minutes
- [ ] Benchmarks: All tests complete successfully
- [ ] Memory: No leaks detected in 30-min test
- [ ] 3D: Orbit and Cortex maintain 50+ FPS

### Observability

- [ ] Jaeger: Traces visible for query requests
- [ ] Kibana: Logs flowing from backend
- [ ] Prometheus: Metrics being scraped
- [ ] Grafana: Dashboards displaying data
- [ ] Alertmanager: Test alert received in Slack

### Alerts (Test Each)

- [ ] HighErrorRate (make failed requests)
- [ ] HighLatency (slow endpoint)
- [ ] ServiceDown (stop backend)
- [ ] HighMemoryUsage (memory load)

---

## 🛟 Troubleshooting

### Backend Not Sending Traces

```bash
# Check Jaeger is running
docker ps | grep jaeger

# Check tracing is enabled
# Look for: "Tracing enabled for dcis-backend"

# Install OpenTelemetry deps
pip install opentelemetry-api opentelemetry-sdk \
            opentelemetry-instrumentation-fastapi \
            opentelemetry-exporter-jaeger
```

### Logs Not Appearing in Kibana

```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Check Logstash
docker logs dcis-logstash

# Verify index exists
curl http://localhost:9200/_cat/indices
```

### No Metrics in Prometheus

```bash
# Check backend /metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus targets
open http://localhost:9090/targets

# Verify scrape config
docker exec dcis-prometheus cat /etc/prometheus/prometheus.yml
```

---

## 📦 Cleanup

```bash
# Stop monitoring stack
docker-compose -f infrastructure/docker/monitoring-stack.yml down

# Remove volumes (CAUTION: deletes all data)
docker-compose -f infrastructure/docker/monitoring-stack.yml down -v
```
