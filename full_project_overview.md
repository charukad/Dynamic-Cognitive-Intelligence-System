# DCIS: Distributed Collective Intelligence System
## The Technical Bible (Version 1.0)

> **Abstract**: This document serves as the single source of truth for the DCIS project. It details the architecture, algorithms, user interface, and operational strategies for a system designed to simulate Superintelligence through the orchestration of specialized narrow models.

---

# BOOK I: GENESIS & PHILOSOPHY

## 1.1 The Core Thesis
Current LLM scaling laws suggest diminishing returns and exponential costs. DCIS operates on the **"Mixture of Agents"** hypothesis:
*$(N \times Small\_Specialized\_Models) + Orchestration > 1 \times Giant\_General\_Model$*

We aim to prove that a swarm of 7B parameter models, when properly coordinated with debate, reflection, and tool use, can outperform a 70B+ parameter model while running on consumer-grade hardware distributed across a network.

## 1.2 "Tangible Intelligence"
The user experience is not secondary; it is part of the system's efficacy. By visualizing the "thought process"—the swarm's movement, the synaptic firing of messages, the crystallization of memory—we increase user trust and facilitate "Human-on-the-Loop" guidance.

---

# BOOK II: THE BRAIN (BACKEND ARCHITECTURE)

## 2.1 The Meta-Orchestrator
The Orchestrator is not an LLM; it is a deterministic state machine coupled with a high-speed routing intelligence.

### 2.1.1 Hierarchical Task Network (HTN) Planner
Instead of simple "Chain of Thought", we use HTN for recursive decomposition.

**Algorithm: Recursive Decomposition**
```python
def decompose(task, depth=0):
    if depth > MAX_DEPTH: return [task]
    
    planner = load_agent("Planner-7B")
    subtasks = planner.generate_plan(task)
    
    # Critical: Critique the plan before execution
    critic = load_agent("Critic-3B")
    critique = critic.review(subtasks)
    
    if critique.score < THRESHOLD:
        subtasks = planner.refine(subtasks, critique.feedback)
        
    final_plan = []
    for st in subtasks:
        if st.is_atomic():
            final_plan.append(st)
        else:
            final_plan.extend(decompose(st, depth+1))
            
    return final_plan
```

### 2.1.2 Thompson Sampling Router
We do not randomly assign tasks. We treat agent selection as a Multi-Armed Bandit problem.

$$ P(Agent_i) \propto Beta(\alpha_i, \beta_i) $$
Where:
- $\alpha_i$ = Success count for task type $T$
- $\beta_i$ = Failure count for task type $T$

## 2.2 The Memory Substrate
Memory is modeled after human cognitive architecture, stored in a distributed vector/graph hybrid system.

### 2.2.1 The Four Memory Tiers
1.  **Working Memory (Redis)**:
    - *Capacity*: ~32k tokens (Context Window)
    - *Content*: Active conversation, current scratchpad.
    - *TTL*: Session duration.

2.  **Episodic Memory (ChromaDB)**:
    - *Structure*: Dense Vector Embeddings (OpenAI text-embedding-3-small).
    - *Retrieval*: HNSW (Hierarchical Navigable Small World) Index.
    - *Content*: Past interactions, user preferences.

3.  **Semantic Memory (Neo4j)**:
    - *Structure*: Knowledge Graph.
    - *Nodes*: Concepts, Entities, Files.
    - *Edges*: `(Agent_A)-[:CREATED]->(Artifact_X)`, `(Concept_Y)-[:IS_RELATED_TO]->(Concept_Z)`.

4.  **Procedural Memory (JSON Store)**:
    - *Content*: "Playbooks" - successful plans for specific task types (e.g., "How to debug Python", "How to write a Haiku").
    - *Mechanism*: If a plan succeeds with >4.5/5 rating, it is serialized and saved here.

---

# BOOK III: THE SOUL (AGENT ECOSYSTEM)

## 3.1 The Agent Taxonomy
We define strict archetypes to prevent "model collapse" (homogeneity).

| Class | Base Model | Temperature | System Prompt Focus |
|-------|------------|-------------|---------------------|
| **Logician** | DeepSeek-Coder-6.7B | 0.1 | Rigor, validation, edge-cases, formal logic. |
| **Creative** | Mistral-7B-Instruct | 0.8 | Divergent thinking, metaphor, narrative flair. |
| **Scholar** | Llama-3-8B | 0.3 | Citation, synthesis, adherence to source material. |
| **Critic** | Phi-3-Mini (3.8B) | 0.2 | Finding flaws, security auditing, fact-checking. |
| **Executive** | Qwen-2.5-14B | 0.4 | Planning, synthesis, conflict resolution. |

## 3.2 The Agent Forge (Genetic Engineering)
When a task fails repeatedly (~3 attempts), the system invokes the Forge.

**Process:**
1.  **Diagnosis**: Analyze why existing agents failed (e.g., "Lack of knowledge about Rust generic types").
2.  **Specification**: Generate a new System Prompt and Configuration.
3.  **Instantiation**: Spin up a new Docker container with the specific LoRA or RAG context.
4.  **Trial**: Run the agent on the failed task.
5.  **Integration**: If successful, add to the pool with high initial $\alpha$ (Thompson Sampling score).

## 3.3 The Synapse Protocol (Inter-Agent Communication)
Agents speak a structured dialect called **DCIS-Protocol** over ZeroMQ.

**Message Schema:**
```json
{
  "id": "uuid-v4",
  "sender": "agent_logician_01",
  "recipients": ["agent_creative_04", "broadcast"],
  "type": "DEBATE",  // QUERY, RESPONSE, CRITIQUE, VOTE
  "payload": {
    "content": "Your premise is flawed because...",
    "confidence": 0.87,
    "attachments": ["file_ref_123"]
  },
  "metadata": {
    "token_cost": 142,
    "latency_ms": 340
  }
}
```

---

# BOOK IV: THE FACE (IMMERSIVE FRONTEND)

## 4.1 Technology Stack
- **Framework**: Next.js 15 (App Router)
- **State**: Zustand (Client) + TanStack Query (Server State)
- **3D Engine**: Three.js + React Three Fiber (R3F) + Drei
- **Realtime**: Socket.io + MsgPack (Binary serialization for particle data)

## 4.2 The "Orbit" (Swarm Visualization)
The default view is a "God's Eye" view of the universe of agents.

### 4.2.1 Advanced Particle System
- **Implementation**: `THREE.InstancedMesh` with 10,000+ instances.
- **Shader Logic (Vertex Shader)**:
  ```glsl
  attribute float size;
  attribute vec3 color;
  varying vec3 vColor;
  void main() {
    vColor = color;
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = size * (300.0 / -mvPosition.z); // Perspective scaling
    gl_Position = projectionMatrix * mvPosition;
  }
  ```
- **Behavior**:
  - **Idle**: Gentle Brownian motion.
  - **Tasking**: Agents accelerate toward a central "Task Attractor" point.
  - **Communication**: Use `MeshLine` to draw Bezier curves between agents.
  - **Data Packets**: Glowing sprites travel along the MeshLines.
    - *Blue Cube*: Logic/Fact data.
    - *Pink Sphere*: Semantic/Creative data.
    - *Red Tetrahedron*: Error/Critique.

## 4.3 The "Neural Link" (Chat Interface)
### 4.3.1 Holographic Projection
- Messages are not 2D divs. They are mapped onto 3D planes in the scene using `Html` from `@react-three/drei`.
- **Parallax**: Moving the mouse tilts all message planes slightly, giving a sense of depth.
- **Glassmorphism**: Backdrop blur filter + white border with 0.1 opacity.

### 4.3.2 Debate Mode "Arena"
When `consensus_score < 0.6`, the UI transitions to **Debate Mode**.
1.  **Camera Transition**: Zooms out to reveal a circular arena.
2.  **Avatar Materialization**: The relevant agents spawn 3D avatars (procedural geometry) on podiums.
3.  **The Beam**: A `VolumetricLight` beam connects the opposing sides. The beam pushes/pulls based on the "Winning Probability" score calculated by the Value Function.

## 4.4 The "Cortex" (Knowledge Graph)
- **Layout Algorithm**: 3D Force-Directed Graph (Octree optimized).
- **Navigation**: "6DOF" (Six Degrees of Freedom) flight controls.
- **Implosion Effect**:
  - When a new memory is stored, particles swirl from the environment to a single point.
  - Flash of light (Bloom > 3.0).
  - A new Node mesh appears, and edge lines grow out to connect to related nodes.

---

# BOOK V: SAFETY & SECURITY

## 5.1 Multi-Layer Defense Matrix
1.  **Input Layer**:
    - **Prompt Injection Detector**: BERT-based classifier trained on jailbreak datasets.
    - **PII Stripper**: Regex + NER (Named Entity Recognition) to redact emails/phones before they hit the LLM.

2.  **Agent Layer**:
    - **Constitutional AI**: Each system prompt ends with:
      > "You must adhere to the DCIS Constitution: Do not harm, do not deceive, prioritize user privacy."
    - **Sandboxing**: Code execution agents run in ephemeral gVisor containers (Google's distinct kernel sandbox) with no network access (unless explicitly whitelisted).

3.  **Output Layer**:
    - **Hallucination Checker**: A separate small model (3B) verifies all factual claims against the Knowledge Graph / Internet.
    - **Sentiment Safety**: Blocks generating toxic or biased content.

## 5.2 The "Red Button" (Kill Switch)
- **Hard Stop**: A global WebSocket signal `SYSTEM_HALT` immediately freezes all Docker containers and terminates LLM inference queues.
- **Memory Rollback**: Reverts the Vector DB state to the snapshot before the current session started (preventing memory poisoning).

---

# BOOK VI: RESEARCH ALGORITHMS

## 6.1 Tree of Thoughts (ToT)
We implement ToT as a search algorithm over the space of partial thoughts.

**Algorithm:**
1.  **Generate**: Given state $s$, generate $k$ potential next steps ($z_1...z_k$).
2.  **Evaluate**: Assign a value $v(s, z_i)$ to each step (0.0 to 1.0).
3.  **Select**: Use Beam Search or BFS to keep the top $b$ states.
4.  **Backtrack**: If all branches fall below threshold $\theta$, return to parent state.

## 6.2 Self-Consistency with Diversity
To improve accuracy, we use **Diversity-Weighted Voting**:
1.  Sample $N$ reasoning paths.
2.  Cluster answers by semantic similarity (Embeddings + DBScan).
3.  Weight each cluster not just by size, but by the *diversity of reasoning* within it (entropy of the thought paths).
4.  Select the cluster with highest Diversity-Weighted Score.


---

# BOOK VII: THE NEXT HORIZON (ADVANCED R&D)

## 7.1 "Oneiroi" (The Dreaming System)
**The Problem**: Continuous learning in LLMs usually leads to catastrophic forgetting. 
**The Solution**: Offline memory consolidation during idle hours.

**Algorithm: Deep Sleep Cycle**
1.  **Replay Buffer**: During the day, high-reward interaction traces $(s, a, r, s')$ are saved to disk.
2.  **Twilight Mode**: Between 02:00 - 05:00 local time:
    - The system spins down high-cost agents.
    - It spins up a single "Dreamer" agent (7B).
3.  **Counterfactual Generation**: The Dreamer reviews past failures: "User asked X, we said Y, User downvoted. What if we said Z?"
4.  **Synthetic Dataset API**: Successful counterfactuals are compiled into a JSONL dataset.
5.  **LoRA Tuning**: A lightweight adapter (`dream.lora`) is fine-tuned on this dataset and merged at sunrise.

## 7.2 "Gaia" (Generative World Model)
**The Problem**: Agents can reason about actions but cannot "feel" the consequences physically.
**The Solution**: A discrete-event simulation engine.

**Implementation**:
- **Sandbox**: A simplified physics/logic environment (can be a code interpreter or a spatial grid).
- **Look-Ahead**: Before running `delete_database()`, the agent runs `sim.execute(delete_database())` in Gaia.
- **Fail-Safe**: If Gaia predicts >80% chance of system destabilization, the action is vetoed.

## 7.3 "The Mirror Protocol" (Digital Twins)
**The Problem**: Generic agents don't "grok" the specific user's mental model.
**The Solution**: A Style-Transfer Hypernetwork.

**Mechanism**:
- **Ingestion**: Vectorize user's Sent Items, Code Commits, and Slack logs.
- **Style Embedding**: Train a small embedding vector $e_{user}$ that represents the user's linguistic fingerprint.
- **Modulation**: In the LLM, inject $e_{user}$ into the Key/Value attention matrices to bias output generation toward the user's style.

## 7.4 "Hive Mind" (Federated Swarm)
**Protocol**: Libp2p over WebSocket.
- **GossipSub**: Nodes gossip about "Procedural Wins" (e.g., "I found that Library X v2.0 breaks Feature Y").
- **Privacy**: No raw data is shared. Only abstract rules and gradient updates (Federated Averaging).

## 7.5 "Gaia-MCTS" (Strategic Foresight)
**Concept**: Combining the World Model with Tree Search.
**Mechanism**:
- **Selection**: Uses UCB1 to balance exploration/exploitation of future states.
- **Rollout**: Runs the Gaia discrete-event simulator to terminal states.
- **Backprop**: Updates the value of decision nodes based on simulated outcomes.

## 7.6 "Cognitive Dissonance" (Contrastive Learning)
**Concept**: Teaching the Knowledge Graph to understand contradictions.
**Mechanism**:
- Fine-tunes the embedding model using Triplet Loss `(Anchor, Positive, Negative)`.
- If `Distance(NewFact, ExistingFact) < Threshold`, the system raises a "Dissonance Alert".

## 7.7 "Socratic Loop" (Active Learning)
**Concept**: Proactive uncertainty reduction.
**Mechanism**:
- If `Entropy(Answer_Distribution) > High`, the system pauses.
- It formulates a specific question to the user to collapse the search space efficiently.

---

# APPENDIX A: API SPECIFICATION

## A.1 Core Endpoints
- `POST /v1/query`: Submit a new task.
  - Params: `text`, `model_preference`, `budget_tier` ("economy", "standard", "pro").
- `GET /v1/stream`: Server-Sent Events (SSE) for real-time text.
- `WS /v1/particles`: WebSocket for binary particle data (MessagePack).

## A.2 Agent Management
- `POST /v1/forge`: Manually trigger agent creation.
- `GET /v1/swarm/metrics`: Real-time VRAM usage, Token/sec, Latency.
- `POST /v1/memory/search`: Semantic search over ChromaDB + Neo4j.

---

# APPENDIX B: DEPLOYMENT

## B.1 Docker Compose Stack
- `orchestrator`: Python FastAPI.
- `inference-engine`: vLLM server (GPU).
- `memory-vector`: ChromaDB.
- `memory-graph`: Neo4j.
- `frontend`: Next.js.
- `queue`: Redis.

## B.2 Hardware Requirements (Minimum)
- **GPU**: NVIDIA RTX 3090 / 4090 (24GB VRAM) or Mac Studio (M2/M3 Max 64GB+).
- **RAM**: 32GB System RAM.
- **Storage**: 1TB NVMe SSD (Vector DBs are I/O heavy).

---

# APPENDIX C: ENTERPRISE CODE GOVERNANCE

## C.1 Project Structure (Production-Ready)

**Backend**: Domain-Driven Design with `api/`, `core/`, `domain/`, `infrastructure/`, `services/` layers  
**Frontend**: Next.js 15 App Router with feature-based organization (`orbit/`, `cortex/`, `neural-link/`)

## C.2 Quality Standards

- **Test Coverage**: >90% required (enforced via CI/CD)
- **Type Safety**: Full mypy (Python) and TypeScript strict mode
- **Security**: Bandit (Python), npm audit, pre-commit hooks

## C.3 Infrastructure

- **Kubernetes**: Kustomize overlays (dev/staging/prod)
- **Observability**: Prometheus, Jaeger, Elasticsearch
- **CI/CD**: GitHub Actions with automated staging deployments

For complete file structure, see `implementation_workflow.md`.

