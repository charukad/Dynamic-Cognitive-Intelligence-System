---
description: Add a new advanced AI feature
---

# Implement Advanced Feature Workflow

## Steps

1. **Research & Design**
   - Review `missing_advanced_features.md` for integration points
   - Create Architecture Decision Record (ADR):
     ```bash
     touch docs/architecture/adr/{###}-{feature-name}.md
     ```

2. **Create feature module**:
   ```bash
   mkdir -p backend/src/services/advanced/{feature_name}
   touch backend/src/services/advanced/{feature_name}/__init__.py
   touch backend/src/services/advanced/{feature_name}/{main_class}.py
   ```

3. **Implement domain interface** (if needed):
   ```bash
   touch backend/src/domain/interfaces/{feature_name}_interface.py
   ```

4. **Write implementation**:
   - Core logic in `services/advanced/{feature_name}/`
   - Use dependency injection for external services
   - Add comprehensive docstrings

// turbo
5. **Create test suite**:
   ```bash
   mkdir -p backend/tests/integration/test_advanced
   touch backend/tests/integration/test_advanced/test_{feature_name}.py
   ```

6. **Integration with orchestrator**:
   - Add to `backend/src/services/orchestrator/meta_orchestrator.py`
   - Wire up dependencies

7. **Add metrics** (`backend/src/infrastructure/monitoring/prometheus_metrics.py`):
   ```python
   {feature_name}_calls = Counter('{feature_name}_calls_total')
   {feature_name}_latency = Histogram('{feature_name}_latency_seconds')
   ```

// turbo-all
8. **Run full test suite**:
   ```bash
   make test
   ```

9. **Update documentation**:
   - Add to `advanced_features_v2.md`
   - Update `complete_ai_architecture.md`
   - Update `project_information.md`

## Success Criteria
- [ ] Feature fully implemented with type hints
- [ ] >90% test coverage
- [ ] Metrics instrumentation added
- [ ] ADR written explaining design choices
- [ ] All documentation updated
