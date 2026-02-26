# Gemini Global & Workspace Rules and Workflows for DCIS

## Global Rules (Add to `~/.gemini/GEMINI.md`)

```markdown
# DCIS Project - Global Rules

## Code Quality Standards

1. **Type Safety is Mandatory**
   - Python: All functions must have type hints. Run `mypy` before committing.
   - TypeScript: Use strict mode. No `any` types without explicit justification.

2. **Test Coverage Requirements**
   - Minimum 90% coverage for all new code
   - Unit tests for all business logic
   - Integration tests for API endpoints
   - E2E tests for critical user flows

3. **Code Style**
   - Python: Follow PEP 8, use Ruff for linting and formatting
   - TypeScript: Use ESLint + Prettier
   - Always run `make format` before committing

4. **Security First**
   - Never hardcode secrets or API keys
   - Always validate and sanitize user inputs
   - Use Bandit (Python) and npm audit for security scanning
   - Run security checks in pre-commit hooks

5. **Documentation Standards**
   - All public functions require docstrings (Google style for Python)
   - Complex algorithms need inline comments explaining "why", not "what"
   - Update relevant .md files when changing architecture

## Architecture Principles

1. **Domain-Driven Design (Backend)**
   - Keep business logic in `domain/` layer
   - Use dependency inversion (interfaces in `domain/interfaces/`)
   - External dependencies live in `infrastructure/`

2. **Clean Architecture**
   - Dependencies point inward (API → Services → Domain)
   - No circular dependencies
   - Use dependency injection

3. **Feature-Based Organization (Frontend)**
   - Group by feature (orbit/, cortex/, neural-link/), not by type
   - Keep components focused and reusable
   - Extract shared logic into custom hooks

4. **Scalability First**
   - Design for horizontal scaling
   - Use async/await for I/O operations
   - Implement caching strategies (Redis)

## Git Workflow

1. **Branch Naming**
   - `feature/description` for new features
   - `fix/description` for bug fixes
   - `refactor/description` for refactoring
   - `docs/description` for documentation

2. **Commit Messages**
   - Use conventional commits: `type(scope): description`
   - Types: feat, fix, refactor, docs, test, chore, perf
   - Example: `feat(orchestrator): add Thompson Sampling router`

3. **Pull Requests**
   - Must pass all CI checks
   - Requires 1 approval minimum
   - Update CHANGELOG.md for user-facing changes
   - Link to relevant issue/ticket

## Performance Budgets

- **Backend**: p50 latency < 500ms, p99 < 2s
- **Frontend**: First Contentful Paint < 1.5s, Time to Interactive < 3s
- **3D Rendering**: Maintain 60fps with 1000+ particles

## AI Agent Development

1. **Agent Design**
   - Each agent should have a single, clear specialization
   - Use temperature wisely (0.1-0.3 for logic, 0.7-0.9 for creativity)
   - Always include confidence scores in responses

2. **Prompt Engineering**
   - System prompts must define role, constraints, and output format
   - Use few-shot examples for complex tasks
   - Test prompts with multiple models before finalizing

3. **Memory Integration**
   - Store successful interaction patterns in Episodic Memory
   - Update Knowledge Graph after each session
   - Implement memory cleanup routines

## Debugging Philosophy

- Always add structured logging (JSON format)
- Use distributed tracing for multi-agent interactions
- Capture reasoning traces for agent decisions
- Save failing cases to test suite
```

---

## Workspace Rules (Add to `.agent/WORKSPACE.md` in `/Users/dasuncharuka/Documents/projects/llm/`)

```markdown
# DCIS Workspace Rules

## Project Context

This workspace contains the Distributed Collective Intelligence System (DCIS), a multi-agent AI orchestration framework with an immersive 3D frontend.

## File Organization

1. **Documentation Priority**
   - `implementation_workflow.md`: The master implementation guide
   - `complete_ai_architecture.md`: Technical architecture reference
   - `project_information.md`: Comprehensive feature list

2. **Code Structure**
   - Backend: Follow Domain-Driven Design in `backend/src/`
   - Frontend: Feature-based organization in `frontend/src/`
   - Infrastructure: IaC files in `infrastructure/`

## Development Workflow

1. **Before Starting Work**
   - Read relevant sections of `implementation_workflow.md`
   - Check `missing_advanced_features.md` for integration requirements
   - Review `algorithmic_specifications.md` for algorithm details

2. **Implementation Order**
   - Always start with domain models (`backend/src/domain/models/`)
   - Then interfaces (`backend/src/domain/interfaces/`)
   - Then infrastructure implementations
   - Finally API endpoints

3. **Testing Requirements**
   - Write tests BEFORE implementation (TDD encouraged)
   - Place tests in `backend/tests/` mirroring `src/` structure
   - Use fixtures from `backend/tests/fixtures/`

## Agent-Specific Guidelines

1. **Meta-Orchestrator**
   - Location: `backend/src/services/orchestrator/`
   - Must use HTN Planner for task decomposition
   - Thompson Sampling for agent selection
   - Chain-of-Verification before returning responses

2. **Specialized Agents**
   - Location: `backend/src/services/agents/`
   - Inherit from `BaseAgent`
   - Override `get_system_prompt()` with role-specific instructions
   - Include confidence estimation logic

3. **Advanced Features**
   - Location: `backend/src/services/advanced/`
   - Organize by feature (gaia/, oneiroi/, mirror/)
   - Must have dedicated test suite
   - Document in `advanced_features_v2.md`

## Frontend Development

1. **3D Components**
   - All Three.js code in `frontend/src/components/orbit/` or `frontend/src/components/cortex/`
   - Use React Three Fiber, not vanilla Three.js
   - Shaders in dedicated `shaders/` subdirectories
   - Target 60fps minimum

2. **State Management**
   - Use Zustand stores in `frontend/src/store/`
   - Keep stores focused (one per feature: swarm, chat, graph, UI)
   - Avoid prop drilling—use hooks

3. **API Integration**
   - All API calls through `frontend/src/lib/api/client.ts`
   - Use TanStack Query for data fetching
   - WebSocket connections via `frontend/src/lib/websocket/`

## Documentation Maintenance

When modifying features:
1. Update `project_information.md` (add/modify feature descriptions)
2. Update `complete_ai_architecture.md` (if changing architecture)
3. Update `implementation_workflow.md` (if changing dev process)
4. Create ADR in `docs/architecture/adr/` for major decisions

## Key Commands

- `make setup`: Initialize development environment
- `make test`: Run all tests
- `make lint`: Check code quality
- `make format`: Auto-format code
- `make docker-up`: Start local stack

## Important Notes

- GPU is required for inference (vLLM)
- Neo4j browser available at http://localhost:7474
- Frontend dev server runs on http://localhost:3000
- Backend API at http://localhost:8000
- API docs at http://localhost:8000/docs
```

---

## Workflows (Create files in `.agent/workflows/`)

### Workflow 1: Add New Agent (`new-agent.md`)

```markdown
---
description: Create a new specialized agent
---

# Add New Agent Workflow

## Steps

// turbo
1. **Create agent class**
   ```bash
   cd backend/src/services/agents
   touch {agent_name}_agent.py
   ```

2. **Implement agent** (edit `{agent_name}_agent.py`):
   ```python
   from .base_agent import BaseAgent
   
   class {AgentName}Agent(BaseAgent):
       def get_system_prompt(self) -> str:
           return """You are a {role} agent specializing in:
           - {specialization_1}
           - {specialization_2}
           
           Always:
           - {guideline_1}
           - {guideline_2}
           """
   ```

3. **Register in factory** (`agent_factory.py`):
   ```python
   AGENT_REGISTRY["{agent_name}"] = {AgentName}Agent
   ```

// turbo
4. **Write unit tests**:
   ```bash
   touch backend/tests/unit/test_{agent_name}_agent.py
   ```

5. **Add to model config** (`backend/config/models.yaml`):
   ```yaml
   - id: {agent_name}
     name: {model_path}
     temperature: {temp}
     device: cuda:0
   ```

// turbo-all
6. **Run tests**:
   ```bash
   cd backend
   poetry run pytest tests/unit/test_{agent_name}_agent.py -v
   ```

7. **Update documentation**:
   - Add to `project_information.md` under "Agent Types"
   - Update `complete_ai_architecture.md` agent table

## Success Criteria
- [ ] Agent class implemented with proper typing
- [ ] System prompt clearly defines role
- [ ] Unit tests pass with >90% coverage
- [ ] Registered in agent factory
- [ ] Documentation updated
```

### Workflow 2: Implement Advanced Feature (`advanced-feature.md`)

```markdown
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
```

### Workflow 3: Deploy to Staging (`deploy-staging.md`)

```markdown
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
```

### Workflow 4: Debug Agent Performance (`debug-agent.md`)

```markdown
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
```

### Workflow 5: Update LLM Models (`update-models.md`)

```markdown
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
```

---

## How to Add These

### Global Rules
1. Open `~/.gemini/GEMINI.md`
2. Copy the "Global Rules" section above
3. Paste and save

### Workspace Rules
1. Navigate to `/Users/dasuncharuka/Documents/projects/llm/`
2. Create `.agent/` directory if it doesn't exist:
   ```bash
   mkdir -p .agent
   ```
3. Create `WORKSPACE.md`:
   ```bash
   touch .agent/WORKSPACE.md
   ```
4. Copy the "Workspace Rules" section above
5. Paste and save

### Workflows
1. Create workflows directory:
   ```bash
   mkdir -p .agent/workflows
   ```
2. Create each workflow file:
   ```bash
   touch .agent/workflows/new-agent.md
   touch .agent/workflows/advanced-feature.md
   touch .agent/workflows/deploy-staging.md
   touch .agent/workflows/debug-agent.md
   touch .agent/workflows/update-models.md
   ```
3. Copy each workflow section into its respective file

## Usage

Once added, you can:
- Reference workflows by name: "Follow the new-agent workflow to create a Scholar agent"
- Use `// turbo` and `// turbo-all` annotations for auto-execution
- Global rules will be enforced automatically
- Workspace rules provide context for the specific project
