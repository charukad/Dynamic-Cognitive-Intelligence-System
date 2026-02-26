# DCIS: Complete AI Architecture Specification

## 1. System Overview

### 1.1 Architectural Philosophy
DCIS is a **multi-agent orchestration framework** that achieves large-model capabilities through the coordination of smaller, specialized models. The architecture follows these principles:

1. **Distributed Intelligence**: No single point of cognitive failure
2. **Emergent Behavior**: Complex capabilities arise from simple agent interactions
3. **Horizontal Scalability**: Add compute by adding nodes, not by upgrading models
4. **Transparency**: Every decision is traceable and explainable

---

## 2. Layer Architecture (7-Layer Model)

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 7: USER INTERFACE (Frontend)                             │
│  - Next.js 15, Three.js, React Three Fiber                      │
│  - Real-time 3D visualization of agent swarm                    │
└─────────────────────────────────────────────────────────────────┘
                            ↕ WebSocket (Socket.io + MsgPack)
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 6: API GATEWAY                                            │
│  - FastAPI REST endpoints + SSE streaming                       │
│  - Authentication, rate limiting, request validation            │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 5: META-ORCHESTRATOR (The Brain)                         │
│  - HTN Planner, Thompson Sampling Router                        │
│  - Chain-of-Verification, Active Learning                       │
│  - Task decomposition, agent selection, result synthesis        │
└─────────────────────────────────────────────────────────────────┘
                            ↕ ZeroMQ (DCIS Protocol)
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4: AGENT ECOSYSTEM                                        │
│  - Specialized Agents: Logician, Creative, Critic, etc.         │
│  - Agent Forge (dynamic creation), Lifecycle Manager            │
│  - Democratic Voting, Debate Mode                               │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: INFERENCE ENGINE                                       │
│  - vLLM (GPU), llama.cpp (CPU), Ollama                          │
│  - Model Zoo: 1B-14B parameter models                           │
│  - LoRA adapters, quantization (4-bit, 8-bit)                   │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: MEMORY & KNOWLEDGE                                     │
│  - Vector DB: ChromaDB (Episodic Memory)                        │
│  - Graph DB: Neo4j (Semantic Memory)                            │
│  - Cache: Redis (Working Memory)                                │
│  - JSON Store (Procedural Memory)                               │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: INFRASTRUCTURE                                         │
│  - Docker containers, Kubernetes (optional)                     │
│  - Message Queue: Redis/RabbitMQ                                │
│  - Monitoring: Prometheus + Grafana                             │
│  - Security: gVisor sandboxing, Constitutional AI               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1 Meta-Orchestrator (Layer 5)

**Purpose**: The central cognitive controller that receives user queries and coordinates agents.

**Core Algorithms**:
1. **HTN Planner**: Recursive task decomposition
2. **Thompson Sampling**: Agent selection (Multi-Armed Bandit)
3. **Chain-of-Verification**: Self-verification loop
4. **Active Learning**: Proactive questioning when uncertain

**State Machine**:
```
IDLE → PLANNING → ROUTING → EXECUTION → SYNTHESIS → VERIFICATION → RESPONSE
  ↑                                                                      ↓
  └──────────────────────────────────────────────────────────────────────┘
```

**Data Structures**:
```python
class TaskNode:
    id: str
    description: str
    status: TaskStatus  # PENDING, RUNNING, COMPLETE, FAILED
    assigned_agent: Optional[str]
    dependencies: List[str]
    result: Optional[Any]
    confidence: float
```

---

### 3.2 Agent Ecosystem (Layer 4)

**Agent Types**:

| Type | Base Model | Temperature | Specialization |
|------|------------|-------------|----------------|
| **Logician** | DeepSeek-Coder-6.7B | 0.1 | Formal reasoning, edge cases |
| **Creative** | Mistral-7B-Instruct | 0.8 | Divergent thinking, narratives |
| **Scholar** | Llama-3-8B | 0.3 | Research, citation, synthesis |
| **Critic** | Phi-3-Mini-3.8B | 0.2 | Fact-checking, security auditing |
| **Executive** | Qwen-2.5-14B | 0.4 | Planning, conflict resolution |
| **Coder** | CodeLlama-7B | 0.2 | Code generation, debugging |
| **Validator** | SmolLM-3B | 0.1 | Output verification, safety |

**Agent Communication Protocol (DCIS-Protocol)**:
```json
{
  "version": "1.0",
  "message_id": "uuid-v4",
  "timestamp": "ISO-8601",
  "sender": {
    "agent_id": "logician_01",
    "agent_type": "LOGICIAN"
  },
  "recipients": ["creative_04", "BROADCAST"],
  "message_type": "DEBATE | QUERY | RESPONSE | CRITIQUE | VOTE",
  "payload": {
    "content": "...",
    "confidence": 0.87,
    "reasoning_trace": ["step1", "step2"],
    "attachments": []
  },
  "metadata": {
    "token_cost": 142,
    "latency_ms": 340,
    "model_version": "deepseek-coder-6.7b-v1.5"
  }
}
```

**Agent Forge**:
- **Trigger**: 3 consecutive task failures on the same task type
- **Process**:
  1. Diagnose capability gap (e.g., "No agent knows Rust generics")
  2. Generate specialized system prompt
  3. Load base model + fine-tune LoRA (if dataset exists)
  4. Deploy in Docker container
  5. Add to agent pool with high Thompson Sampling α

---

### 3.3 Memory Architecture (Layer 2)

**1. Working Memory (Redis)**
- **Type**: In-memory cache
- **Capacity**: 32k tokens
- **TTL**: Session duration
- **Structure**: Hash map `{session_id: {context, scratchpad, active_agents}}`

**2. Episodic Memory (ChromaDB)**
- **Type**: Vector database
- **Embeddings**: OpenAI text-embedding-3-small (1536 dims)
- **Index**: HNSW (Hierarchical Navigable Small World)
- **Retrieval**: Top-K similarity search (cosine distance)
- **Schema**:
  ```python
  {
    "id": "uuid",
    "embedding": [0.12, -0.45, ...],
    "metadata": {
      "timestamp": "...",
      "user_id": "...",
      "rating": 4.5,
      "tags": ["success", "python", "debugging"]
    },
    "document": "Full interaction text"
  }
  ```

**3. Semantic Memory (Neo4j Knowledge Graph)**
- **Nodes**: `Concept`, `Agent`, `Task`, `Artifact`, `User`
- **Relationships**:
  - `(Agent)-[:EXECUTED]->(Task)`
  - `(Task)-[:PRODUCED]->(Artifact)`
  - `(Concept)-[:IS_RELATED_TO]->(Concept)`
  - `(Concept)-[:CONTRADICTS]->(Concept)` ← *from Contrastive Learning*
- **GNN Layer**: GraphSAGE for link prediction

**4. Procedural Memory (JSON Files)**
- **Structure**: Playbooks of successful task patterns
- **Example**:
  ```json
  {
    "task_type": "python_debugging",
    "success_rate": 0.92,
    "avg_tokens": 1500,
    "template": {
      "step_1": "Read error traceback",
      "step_2": "Locate file:line",
      "step_3": "Analyze context",
      "step_4": "Generate fix",
      "step_5": "Verify with unit test"
    }
  }
  ```

---

## 4. Advanced AI Subsystems

### 4.1 Gaia (World Model + MCTS)
**Purpose**: Simulate action outcomes before execution.

**Components**:
1. **Discrete Event Simulator**: Lightweight physics/logic engine
2. **MCTS Tree Search**: Explore decision space
3. **Rollout Policy**: Heuristic-guided or random simulation
4. **Fail-Safe**: Veto actions with >80% predicted failure rate

**Integration**:
```python
def execute_with_gaia(action):
    sim_result = gaia.simulate(action, num_rollouts=1000)
    
    if sim_result.failure_probability > 0.8:
        return BlockedAction(reason=sim_result.failure_mode)
    elif sim_result.uncertainty > 0.5:
        # Trigger Active Learning
        user_guidance = active_learning.ask_user(action, sim_result)
        return execute_with_approval(action, user_guidance)
    else:
        return execute(action)
```

### 4.2 Oneiroi (Dreaming System)
**Purpose**: Offline learning during idle time.

**Schedule**: 02:00 - 05:00 local time

**Process**:
1. Retrieve high-value interactions (rating ≥ 4.0)
2. Generate counterfactuals ("What if I had used Agent B?")
3. Compile synthetic dataset
4. Fine-tune LoRA adapter
5. Merge adapter at 05:00

### 4.3 Mirror Protocol (Digital Twin)
**Purpose**: User-specific style replication.

**Training**:
1. Ingest user corpus (emails, code, notes)
2. Train style embedding vector `e_user` (512-dim)
3. Inject into LLM attention: `Q' = Q + W_style * e_user`

**Safety**: Requires biometric auth or master password.

---

## 5. Security Architecture

### 5.1 Multi-Layer Defense
```
INPUT LAYER:
├─ Prompt Injection Detector (BERT classifier)
├─ PII Stripper (Regex + NER)
└─ Content Filter (OpenAI Moderation API)

AGENT LAYER:
├─ Constitutional AI (Behavioral Constraints)
├─ Sandboxing (gVisor containers)
└─ Resource Limits (CPU, RAM, Network)

OUTPUT LAYER:
├─ Hallucination Checker (3B verification model)
├─ Fact Verification (Cross-reference Knowledge Graph)
└─ Toxicity Filter
```

### 5.2 Constitutional AI
**The DCIS Constitution**:
1. **Honesty**: Do not deceive or hallucinate.
2. **Safety**: Do not generate harmful content.
3. **Privacy**: Protect user data.
4. **Humility**: Admit uncertainty.

**Enforcement**: Every agent output is critiqued against the Constitution by a Critic agent.

---

## 6. Frontend Architecture (Layer 7)

### 6.1 Technology Stack
- **Framework**: Next.js 15 (App Router, Server Components)
- **3D Engine**: Three.js + React Three Fiber
- **State**: Zustand (client), TanStack Query (server)
- **Real-time**: Socket.io + MsgPack

### 6.2 Core Visualizations

**"The Orbit" (Swarm View)**:
- **Renderer**: WebGL via THREE.InstancedMesh (10k+ particles)
- **Physics**: Custom GPGPU compute shaders for particle simulation
- **Shaders**:
  - Vertex: Perspective-based point size scaling
  - Fragment: Holographic glow (Fresnel effect)

**"The Synapse" (Communication)**:
- **Lines**: THREE.MeshLine library for Bezier curves
- **Data Packets**: Animated sprites (Blue cube = Logic, Pink sphere = Creative)

**"The Cortex" (Knowledge Graph)**:
- **Layout**: 3D Force-Directed (Octree optimization)
- **Navigation**: OrbitControls + 6DOF for "Dive Mode"

---

## 7. Deployment Architecture

### 7.1 Single-Node Deployment (Development)
```yaml
# docker-compose.yml
services:
  orchestrator:
    image: dcis/orchestrator:latest
    ports: ["8000:8000"]
    
  inference:
    image: dcis/vllm:latest
    runtime: nvidia
    
  chromadb:
    image: chromadb/chroma:latest
    
  neo4j:
    image: neo4j:5
    
  redis:
    image: redis:alpine
    
  frontend:
    image: dcis/frontend:latest
    ports: ["3000:3000"]
```

### 7.2 Multi-Node Deployment (Production)
```
      LOAD BALANCER (nginx)
             |
      ┌──────┴───────┐
      │              │
 COORDINATOR    COORDINATOR (Standby)
      |
  ┌───┴────────┬──────────┐
WORKER-1    WORKER-2   WORKER-N
  (GPU)       (GPU)      (CPU)
```

**Coordinator**: FastAPI + Celery
**Workers**: Individual agent containers
**State**: Redis Cluster (distributed)
**Scaling**: Kubernetes HPA (Horizontal Pod Autoscaler)

---

## 8. Data Flow Example

**User Query**: "Write a Python function to parse JSON with error handling"

```
1. API Gateway receives request
   ↓
2. Meta-Orchestrator:
   - HTN decomposition: [Understand, Design, Implement, Test]
   - Thompson Sampling: Assign "Coder" agent
   ↓
3. Coder Agent:
   - Retrieves similar code from Episodic Memory (RAG)
   - Generates draft code
   ↓
4. Chain-of-Verification:
   - Critic agent generates test questions
   - Coder answers own questions
   - Inconsistency detected!
   ↓
5. Revision:
   - Coder revises code
   - Validator confirms safety
   ↓
6. Synthesis:
   - Executive agent formats final response
   - Explanation generated
   ↓
7. Knowledge Update:
   - Store in Episodic Memory (vector)
   - Update Knowledge Graph: (Python)-[:HAS_PATTERN]->(ErrorHandling)
   ↓
8. Response sent to user
```

---

## 9. Performance Specifications

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Latency (p50)** | <500ms | First token |
| **Latency (p99)** | <2s | Complete response |
| **Throughput** | 100 queries/min | Single node |
| **Memory Usage** | <16GB RAM | Excluding model weights |
| **GPU VRAM** | <24GB | All agents loaded |
| **Accuracy** | >90% | User satisfaction rating |

---

## 10. Monitoring & Observability

**Metrics (Prometheus)**:
- Agent utilization %
- Token consumption rate
- Cache hit rate
- Query latency distribution

**Traces (Jaeger)**:
- Distributed tracing across agents
- Task dependency visualization

**Logs (ELK Stack)**:
- Structured JSON logs
- Agent reasoning traces
- Error debugging

---

## 11. Extensibility

**Plugin Architecture**:
```python
class Plugin(ABC):
    @abstractmethod
    def on_query_start(self, query: str) -> None:
        pass
    
    @abstractmethod
    def on_agent_response(self, agent_id: str, response: str) -> str:
        """Can modify response before returning"""
        pass
```

**Example Plugins**:
- Slack integration
- GitHub copilot mode
- Notion knowledge sync

---

This architecture supports **horizontal scaling**, **fault tolerance**, and **progressive enhancement** while maintaining the core philosophy of emergent collective intelligence.

---

# APPENDIX C: ENTERPRISE PROJECT STRUCTURE

## C.1 Code Organization (Production-Grade)

### Backend Structure (Domain-Driven Design)
```
backend/src/
├── api/          # HTTP Controllers (FastAPI routes, middleware)
├── core/         # Cross-cutting (config, security, logging, events)
├── domain/       # Business Logic (models, interfaces, value objects, events)
├── infrastructure/  # External Adapters (LLM clients, DB repositories, messaging)
├── services/     # Application Services (orchestrator, agents, forge, advanced AI)
└── schemas/      # DTOs for validation
```

### Frontend Structure (Atomic Design + Feature-Based)
```
frontend/src/
├── app/          # Next.js App Router (route groups, API routes)
├── components/   # UI (shadcn), orbit/, cortex/, neural-link/, conductor/
├── hooks/        # Custom React hooks (useSwarmState, useWebSocket, useSpatialAudio)
├── lib/          # Utilities (API client, WebSocket manager, Three.js helpers)
├── services/     # Business logic layer
├── store/        # Zustand stores (swarm, chat, graph, UI)
└── types/        # TypeScript interfaces
```

## C.2 Quality & Governance

**Automated Checks**:
- Linting: Ruff (Python), ESLint (TypeScript)
- Type Safety: mypy, TypeScript strict mode
- Security: Bandit, npm audit
- Test Coverage: >90% required

**Pre-commit Hooks**: Enforce formatting, type checking, security scans before commits.

## C.3 Infrastructure as Code

**Kubernetes**: Kustomize base + overlays (dev/staging/prod)
**Helm Charts**: Package management for DCIS deployment
**Terraform**: Multi-cloud provisioning (VPC, EKS, S3, RDS)

## C.4 Observability

- **Metrics**: Prometheus → Grafana dashboards
- **Traces**: OpenTelemetry → Jaeger
- **Logs**: Fluentd → Elasticsearch → Kibana
- **Alerts**: Alertmanager → PagerDuty

For full project structure details, see `implementation_workflow.md`.

