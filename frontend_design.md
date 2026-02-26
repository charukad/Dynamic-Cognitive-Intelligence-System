# DCIS Frontend Architecture & Design Specification

## 1. Design Philosophy: "Tangible Intelligence"
The frontend must not look like a standard chat application. It should resemble a **Sci-Fi Command Center** or a **Bio-Digital Laboratory**. The user needs to *feel* the collective intelligence working.

### 1.1 Aesthetic Direction
- **Theme**: "Glass & Light". Deep, dark backgrounds (void black/midnight blue) with glowing, glass-morphic elements.
- **Typography**: Monospace for data/code (e.g., JetBrains Mono), clean geometric sans-serif for UI (e.g., Geist, Inter).
- **Motion**: Everything is alive. Agents "breathe" (pulse) when active. Connections "flow" interaction data.
- **Palette**:
  - Primary: Cyan/Electric Blue (Intelligence, System)
  - Secondary: Neon Purple (Creative Agents)
  - Success: Emerald Green (Consensus/Verified)
  - Warning/Conflict: Amber (Disagreement/Debate)
  - Error/Destructive: Crimson (Termination/Critical Failure)

## 2. Technical Stack
- **Framework**: Next.js 15 (App Router) for performance and server components.
- **State Management**: Zustand (for global UI state) + TanStack Query (for agent data syncing).
- **Visualization (The Core)**:
  - **Three.js / React Three Fiber (R3F)**: The backbone of the immersive experience.
  - **Drei**: Evaluation and staging helpers.
  - **React Spring / Framer Motion 3D**: For physics-based 3D animations.
  - **Post-Processing**: `react-postprocessing` for Bloom, DOF, and Glitch effects.
  - **ShaderMaterial**: Custom GLSL shaders for holographic effects.
- **2D Graphs**: React Flow / XYFlow for orchestration pipelines.
- **Styling**: Tailwind CSS + CVA.
- **Real-time**: WebSocket (Socket.io) with binary message packing (MsgPack) for high-frequency particle updates.

---

## 3. Core Interface Structure

### 3.1 Global Layout
- **Sidebar (Collapsible)**: System status, Navigation.
- **Main Stage**: The primary workspace (Canvas-dominant).
- **HUD (Heads-Up Display) Overlay**:
  - Top Right: Global Resource Usage (VRAM, Tokens/sec, Cost).
  - Bottom Right: Interaction Toast/Notifications.

## 4. Feature-Specific Views & Three.js Implementations

### 4.1 The "Orbit" (Swarm Intelligence Visualization)
*A visual representation of the active agent swarm.*
- **Implementation**:
  - **InstancedMesh**: Render thousands of agents ("Stars") efficiently.
  - **Spatial Clustering**: Agents group dynamically based on domain (e.g., Coding agents cluster near Top-Right).
- **Live Event Visualization (Dynamic High-Fidelity)**:
  - **Agent Communication (The Synapse)**:
    - **Visual**: When Agent A messages Agent B, a glowing "Neural Line" (MeshLine) connects them.
    - **Data Packets**: Geometry shapes travel along these lines representing payload types:
      - *Cube (Blue)*: Structured Data / Logic.
      - *Sphere (Purple)*: Natural Language / Creative thought.
      - *Tetrahedron (Red)*: Error / Warning.
    - **Burst Effect**: Upon packet receipt, the receiving agent "flares" (bloom intensity spikes), mimicking a neuron firing.
  - **Automatic Agent Creation (The Spawning)**:
    - **Animation**: A "Reverse Implosion". Particles swirl from the void, knitting together into a wireframe sphere, then solidifying into the agent avatar.
    - **Visual Sound**: A shockwave ring expands from the new agent, pushing nearby agents slightly away (physics collision).
  - **Agent Termination (The De-resolution)**:
    - **Animation**: The agent dissolves into digital static (glitch shader) and fades into transparency, leaving a faint "memory echo" (ghost trail) for a few seconds.

### 4.2 The "Neural Link" (Advanced Chat Interface)
*Not just a timeline, but a threaded, multi-voice conversation.*
- **Holographic Stream**: Messages are "projected" onto 2.5D planes with parallax.
- **Debate Mode (3D)**:
  - Agents active in a debate materialize as 3D Avatars on a "Stage".
  - **Tug-of-War Visualization**: An energy beam connects opposing agents. The beam's color and push/pull position shift in real-time based on the "Winning Probability" of the argument.

### 4.3 "Cortex" (Immersive Knowledge Graph)
- **Visuals**: High-intensity bloom, Force-Directed Graph (3D).
- **Memory Formation**:
  - When new long-term memories are created, they "crystallize" in the graph—starting as fluid particles and hardening into a node connection.

### 4.4 "Conductor" (Orchestration Pipeline)
*Visualizing the invisible meta-processes.*
- **Live Task Flow**: Tasks are "Energy Packets" moving along pipes.
- **Bottleneck Visualization**: Pipes glow red and expand if an agent is overloaded.


### 4.6 Special Visual Modes

#### 4.6.1 "Oneiroi" State (Dream Mode)
 *Activates during idle hours (Offline Consolidation).*
 - **Palette Shift**: The void background transitions to a deep, bioluminescent indigo (`#0A001A`).
 - **Particle Behavior**: Agents (particles) slow down to 10% speed.
 - **Synapse Sparks**: Random MeshLines ignite briefly between distant agent clusters, representing memory reconsolidation (Hebbian learning).
 - **Audio**: A low-frequency theta-wave drone (4-7 Hz) plays in the background.

#### 4.6.3 "Gaia" Tree Search (MCTS Overlay)
 *Activates during deep strategic planning.*
 - **Visual**: A branching holographic tree grows out of the agent's avatar.
 - **Branches**: Lines represent future paths. Thickness = Certainty (UCB1 score).
 - **Leaves**: End states glow Green (Success) or Red (Failure).
 - **Pruning**: Low-probability branches wither and dissolve in real-time.

#### 4.6.4 "Socratic" Mode (Active Learning)
 *Activates when the system needs user input.*
 - **Visual**: The entire "Orbit" freezes (Time Stop effect).
 - **Focus**: A single spotlight beam hits the center stage.
 - **Interaction**: The specific "Question Entity" floats forward (e.g., "Library A vs B").
 - **Input**: The user selects an option, and the "time freeze" shatters, resuming the simulation with new knowledge.

---

## 5. Advanced Immerse Features (Next-Level)

### 5.1 Holographic UI Materials (GLSL)
- **Shader Strategy**: Use custom ShaderMaterials for UI elements.
- **Effects**: Scanlines, Noise, Chromatic Aberration, Fresnel Glow.

### 5.2 Volumetric Lighting & Atmosphere
- **God Rays**: Use `GodRays` effect from post-processing on the central "Superintelligence" node.
- **Fog**: Exponential fog fades distant agents into the void.

### 5.3 Spatial Audio
- **Positional Sound**: Integrate `Three.js` PositionalAudio. Sounds originate from the specific agent's location in 3D space.

### 5.4 XR / VR Readiness ("Dive" Mode)
- **WebXR Support**: Step *inside* the Cortex graph with VR headsets.

---

## 6. Implementation Strategy (Frontend)

### Phase 1: The Shell & Canvas
- Setup Next.js + R3F.
- Implement the "Starfield" background (low-cost particle system).

### Phase 2: The Evolving Swarm (Orbit)
- Build the `AgentSwarm` component using `InstancedMesh`.
- Implement **Synapse System**: The glowing communication lines and packet animations.
- Implement **Lifecycle Shaders**: The spawn/despawn GLSL effects.

### Phase 3: The Hologram
- Write custom GLSL shaders for the "HoloCard" UI components.

### Phase 4: Interaction & Audio
- Add Raycaster interactions, Spatial Audio, and camera transitions.

---

## 6. Enterprise Frontend Code Organization

### Production Structure
```
frontend/src/
├── app/          # Next.js 15 App Router (route groups)
├── components/   # ui/, orbit/, cortex/, neural-link/, conductor/
├── hooks/        # useSwarmState, useWebSocket, useSpatialAudio
├── lib/          # API client, WebSocket, Three.js utils
├── services/     # Business logic layer
├── store/        # Zustand stores
└── types/        # TypeScript interfaces
```

### Quality Standards
- **Type Safety**: TypeScript strict mode
- **Testing**: Playwright E2E + Vitest
- **Performance**: 60fps @ 1000+ particles
- **CI/CD**: GitHub Actions → automated deployments

For complete structure, see `implementation_workflow.md`.
