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
