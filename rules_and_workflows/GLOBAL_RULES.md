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
