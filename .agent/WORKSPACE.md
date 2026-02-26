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
