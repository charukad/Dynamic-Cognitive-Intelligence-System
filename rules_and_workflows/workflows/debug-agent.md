---
description: Debug slow or failing agent
---

# Debug Agent Performance Workflow

## Steps

1. **Identify the problem**:
   ```bash
   # Check Prometheus metrics
   curl http://localhost:8000/metrics | grep agent_{name}
   
   # Analyze logs
   kubectl logs deployment/orchestrator -n dcis-prod | jq 'select(.agent_id == "{agent_id}")'
   ```

2. **Check resource usage**:
   ```bash
   # GPU memory
   nvidia-smi
   
   # Agent instance count
   kubectl get pods -l app=agent-{name}
   ```

// turbo
3. **Run local profiling**:
   ```bash
   cd backend
   poetry run python -m cProfile -o agent_profile.prof src/services/agents/{agent_name}_agent.py
   poetry run snakeviz agent_profile.prof
   ```

4. **Analyze reasoning traces**:
   - Check Episodic Memory for failed interactions
   - Look at Neo4j for knowledge gaps

5. **Common fixes**:
   - **Slow inference**: Lower model size, increase batch size, use quantization
   - **Low accuracy**: Improve system prompt, add few-shot examples, fine-tune LoRA
   - **High memory**: Enable streaming, reduce context window, offload to CPU
   - **High latency**: Add caching, optimize retrieval, use faster embedding model

// turbo
6. **Test fix locally**:
   ```bash
   docker-compose up -d
   # Send test queries to http://localhost:8000/v1/query
   ```

7. **Compare before/after metrics**:
   ```bash
   ./scripts/analysis/agent-performance-report.py --agent {agent_name} --compare
   ```

## Success Criteria
- [ ] Latency improved by >20%
- [ ] Accuracy maintained or improved
- [ ] Resource usage within budget
- [ ] Tests still passing
