---
description: Deploy DCIS to staging environment
---

# Deploy to Staging Workflow

## Prerequisites
- All tests passing on main branch
- Docker images built

## Steps

// turbo-all
1. **Verify tests**:
   ```bash
   make ci
   ```

2. **Build Docker images**:
   ```bash
   ./scripts/deployment/build-images.sh
   ```

3. **Tag images**:
   ```bash
   docker tag dcis/orchestrator:latest dcis/orchestrator:staging-$(git rev-parse --short HEAD)
   docker tag dcis/frontend:latest dcis/frontend:staging-$(git rev-parse --short HEAD)
   docker tag dcis/inference:latest dcis/inference:staging-$(git rev-parse --short HEAD)
   ```

4. **Push to registry**:
   ```bash
   docker push dcis/orchestrator:staging-$(git rev-parse --short HEAD)
   docker push dcis/frontend:staging-$(git rev-parse --short HEAD)
   docker push dcis/inference:staging-$(git rev-parse --short HEAD)
   ```

5. **Deploy to Kubernetes**:
   ```bash
   kubectl apply -k infrastructure/kubernetes/overlays/staging/
   ```

6. **Verify deployment**:
   ```bash
   kubectl get pods -n dcis-staging
   kubectl logs -f deployment/orchestrator -n dcis-staging
   ```

7. **Run smoke tests**:
   ```bash
   ./scripts/deployment/smoke-test-staging.sh
   ```

8. **Monitor metrics**:
   - Check Grafana dashboard: https://grafana.staging.dcis.internal
   - Verify no error spikes in logs

## Success Criteria
- [ ] All pods running (no CrashLoopBackOff)
- [ ] Smoke tests pass
- [ ] API health endpoint returns 200
- [ ] Frontend loads correctly
- [ ] No error rate increase in logs
