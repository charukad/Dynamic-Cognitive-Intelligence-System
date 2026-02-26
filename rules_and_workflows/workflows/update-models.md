---
description: Update base LLM models
---

# Update LLM Models Workflow

## Steps

1. **Check for new releases**:
   - HuggingFace: https://huggingface.co/models
   - Monitor: DeepSeek-Coder, Mistral, Llama, Phi releases

// turbo
2. **Download new model**:
   ```bash
   ./scripts/maintenance/download-model.sh {model_name}
   ```

3. **Benchmark locally**:
   ```bash
   cd backend
   poetry run python scripts/benchmark_model.py --model {model_path}
   ```

4. **Update config** (`backend/config/models.yaml`):
   ```yaml
   - id: {agent_name}
     name: {new_model_path}  # Update this line
     version: v2  # Increment version
   ```

5. **A/B test in staging**:
   - Deploy 50% traffic to new model
   - Monitor for 24 hours
   - Compare: latency, accuracy, token cost

6. **Full rollout if successful**:
   ```bash
   kubectl set image deployment/inference-{agent} inference={new_image} -n dcis-prod
   ```

// turbo
7. **Cleanup old models**:
   ```bash
   ./scripts/maintenance/prune-old-models.sh
   ```

## Success Criteria
- [ ] New model shows ≥ performance vs old model
- [ ] No regressions in test suite
- [ ] Cost per query not increased by >10%
- [ ] Old model removed from cluster
