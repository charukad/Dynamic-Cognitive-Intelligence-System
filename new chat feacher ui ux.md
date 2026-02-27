# New Chat Feature UI/UX Specification

## Experience Vision
This feature is not a standard chat dashboard. It is a Living AI Organization Interface. The user should feel like they hired an AI company and can watch that company think, coordinate, debate, recover from failure, and deliver results.

The experience must make orchestration visible without becoming noisy. It should feel alive, legible, premium, and operationally trustworthy.

## Core Experience Principles
- Show intelligence in motion, not just final output.
- Make every room, movement, and status change meaningful.
- Keep the user oriented at all times: what is happening, who is doing it, and what comes next.
- Provide deep transparency layers without overwhelming casual users.
- Preserve a strong sense of place: the office is the product surface, not decorative background.

## Overall Layout
The application is divided into three primary zones:

```text
---------------------------------------------------------------
| Front Desk Chat |      Interactive Office Workspace         |
|                 |--------------------------------------------|
|                 |     Lower Control and Analytics Panel      |
---------------------------------------------------------------
```

### Zone 1: Front Desk Interaction
The left panel is the user’s conversation surface. It is the intake desk for the AI office.

### Zone 2: Interactive Office Workspace
The center is a 2.5D semi-isometric office floor where agents appear as active employees moving through rooms with defined roles.

### Zone 3: Lower Control and Analytics Panel
The bottom panel provides deeper inspection, live logs, office metrics, and graph views without interrupting the main office scene.

## Visual Language
- Primary environment: warm office materials, muted wood and structural tones
- System overlays: dark glass, graphite, cyan, electric blue, and alert red
- Rendering style: semi-isometric or top-down 2.5D, not flat cards
- Motion style: smooth, intentional, operational, never cartoonish
- Character style: simplified professional worker avatars or agent glyph-people, readable at a glance
- Density: rich but controlled, with clear layering between environment, agent activity, and analytics overlays

## Display Modes
The interface must support three viewing modes.

### Simple Mode
- Reduced motion
- Minimal office animation
- Focus on chat, final answer, and current task state

### Executive Mode
- Stronger emphasis on analytics, costs, risk, and operational performance
- Reduced decorative motion, increased data density

### Full Simulation Mode
- Full animated office behavior
- Agent movement between rooms
- Speech bubbles, live task paths, hiring events, and visible orchestration flows

## Front Desk Chat Panel
### Purpose
The chat panel is where the user submits work and receives the final composed response from the office.

### Required Elements
- Conversation history list or session switcher
- User messages
- Final assistant responses
- Streaming indicator
- Active mode selector:
  - `Balanced`
  - `High Accuracy`
  - `Budget Mode`
- `Start Project Mode` toggle for larger orchestrated flows
- Selected agent or orchestration context
- Clear send action and keyboard behavior

### Interaction Behavior
- When the user sends a message, the request should visually animate from the chat panel into the Strategy Center.
- The final response should visibly return from the office to the chat panel.
- The chat panel must remain useful on its own, but the office should explain what is happening behind the answer.

## Interactive Office Workspace
### Core Purpose
The office is the main storytelling and operational surface. It explains how the system is thinking and working in real time.

### Office Requirements
- Every room must have operational meaning.
- Agents must appear to work as individual employees, not abstract dots.
- Nearby collaboration should visibly cluster agents together.
- Voting and governance events should move agents into shared decision spaces.
- The user must be able to click rooms, agents, and overlays for deeper detail.

## Room Specifications
### Strategy Center
The central planning room where orchestration begins.

Visuals:
- Large planning table
- Tactical wall or digital board
- Task graph projection above the table

Behavior:
- New user requests arrive here first
- Strategic and tactical planning agents gather around the table
- The task graph appears and branches into subtasks
- Assignment lines pulse outward toward work pods

Click Action:
- Open task DAG viewer
- Show subtasks, dependencies, routing decisions, cost forecast, and assigned agents

### Boss's Office
The Orchestrator control room, positioned as the executive oversight space.

Visuals:
- Glass office with central desk
- Wall screens for heatmaps, active tasks, retries, and costs

Behavior:
- Lights or glow intensify during failures, escalations, or policy intervention
- Boss activity becomes visible when repeated retries or risk conditions occur

Click Action:
- Open orchestration panel
- Show AEI, retry history, coaching events, risk settings, policy controls, and intervention logs

### Voting Chamber
The governance room for hiring, firing, and conflict resolution.

Visuals:
- Circular chamber
- Shared round table
- Scorecards or vote indicators

Behavior:
- Participating agents physically move to the chamber
- Voting animation and discussion indicators appear
- Results are displayed as a structured decision outcome

Click Action:
- Show vote distribution, evaluation criteria, final decision, and agent-level reasoning

### Collaboration Hub
Shared pod space where agents coordinate, debate, and cross-check work.

Visuals:
- Clustered work pods
- Visible speech bubbles or conversation pulses
- Highlighted shared workspace when multiple agents are active together

Behavior:
- Agents move closer when exchanging information
- Collaboration happens in visible groups, not hidden background state
- Cross-validation and debate must be distinguishable from normal execution

Click Action:
- Show internal discussion log, shared working memory, and linked task context

### Individual Pods
Private workstations for agents operating independently.

Visuals:
- One desk or station per agent
- Display monitor, status badge, and progress indicator

Supported statuses:
- `Researching`
- `Calculating`
- `Waiting for dependency`
- `Validating`
- `Retrying`
- `Idle`

Click Action:
- Open agent profile card with role, capabilities, tools, model version, AEI, cost per task, failure history, permissions, recent outputs, and communication history

### Specialist Incubator
The hiring and specialization area used when capability gaps are detected.

Visuals:
- Glass lab or incubation area
- New desk or seat appears when hiring begins
- Benchmark progress and probation badge are visible

Behavior:
- Triggered when the system needs a new specialist capability
- Shows generation, benchmark, comparison, and approval progress

Click Action:
- Show generated prompt, tool assignments, benchmark tests, performance comparisons, and approval probability

### Memory Vault
The persistent memory and customer context area.

Visuals:
- Vault room with central data core or memory lattice
- Retrieval pulses during recall events

Behavior:
- Lights up when customer preferences, long-term memory, or context retrieval is used

Click Action:
- Show customer persona, preference graph, historical goals, memory retrieval events, and relevant similarity hits

### Active Pods
Specialized execution zones for heavy operations.

Examples:
- Web research pod
- Code generation pod
- Simulation sandbox
- Tool execution pod

Visuals:
- Activity screens
- Progress meters
- Tool call counters
- Resource usage indicators

## Live Office Graph Overlay
An optional overlay mode visualizing system flow on top of the office.

### Purpose
Make complex routing visible without replacing the office scene.

### Visual Rules
- Nodes represent agents, rooms, or tasks
- Animated pulses represent request or message flow
- Green paths indicate successful progression
- Red paths indicate failures, escalations, or retries
- Hiring events and debate cycles must be clearly visible

### Interaction
- User can toggle the overlay on and off
- Clicking a node opens the associated room, agent, or task panel

## Lower Control and Analytics Panel
This panel is persistent and tab-driven.

### Active Employees Tab
Shows the full roster of agents with:
- Name
- Role
- Status
- Current assignment
- AEI
- Success rate
- Cost per task

### Activity Feed Tab
Real-time event log with entries such as:
- `TASK_STARTED`
- `AGENT_ASSIGNED`
- `TOOL_CALLED`
- `RETRY_TRIGGERED`
- `VOTING_STARTED`
- `AGENT_HIRED`
- `AGENT_FIRED`
- `FINAL_RESPONSE_SENT`

Filters:
- Agent
- Task
- Severity
- Cost impact

### Office Stats Tab
Shows:
- Session cost
- Token usage
- Retry count
- Success rate
- Average confidence
- Budget mode status
- Persona summary

### Task DAG Viewer Tab
Shows:
- Expandable task graph
- Execution time
- Assigned agent
- Evaluation score
- Retry history
- Model used

### Replay Tab
Allows the user to replay orchestration history step by step.

Capabilities:
- Rewind execution
- Step through decisions
- Watch agent movement and communications
- Inspect why retries or escalation happened

## Agent Interaction Model
### Hover State
- Quick tooltip with name, role, status, current task, and AEI

### Click State
- Opens persistent side drawer or modal with full profile

### Status Expression
Agent state should be readable through:
- Position
- Badge color
- Label text
- Motion pattern
- Room context

## Motion and Micro-Interactions
These interactions are essential, not decorative.

### Required Motion Behaviors
- Requests animate from Front Desk to Strategy Center
- Agents walk between rooms and pods
- Collaboration causes agents to gather in local clusters
- Voting gathers agents into the Voting Chamber
- Hiring spawns a new specialist seat in the incubator
- Boss office glows on crisis or intervention
- Task flow pulses between rooms and agents
- Final response returns to the chat panel

### Motion Quality Rules
- Motion must communicate state changes clearly
- Avoid excessive bounce, overshoot, or playful motion language
- Keep pacing calm and readable for long sessions

## Core User Flows
### Flow 1: Standard Request
1. User submits message from Front Desk.
2. Request animates into Strategy Center.
3. Task plan appears.
4. Agents move to assigned pods.
5. Collaboration or validation appears if needed.
6. Final answer returns to chat.
7. Office stats and activity feed update live.

### Flow 2: Collaboration and Debate
1. Planner assigns subtasks to multiple agents.
2. Agents move into Collaboration Hub.
3. Speech bubbles or interaction markers show exchange.
4. Shared result is produced and passed onward.

### Flow 3: Hiring Event
1. System detects missing capability.
2. Specialist Incubator activates.
3. New agent prototype appears with benchmark progress.
4. Voting Chamber or Boss office approves or rejects.
5. If approved, agent joins office roster.

### Flow 4: Failure and Recovery
1. An agent fails validation or exceeds retry threshold.
2. Boss office becomes visually active.
3. Activity feed records the failure and retry.
4. Office graph highlights the failure path.
5. User sees status without losing the main conversation context.

## States
### Empty State
- Calm but informative
- Encourages the user to start a project or ask a question
- Shows which office mode and agent context are active

### Loading State
- Partial rendering preferred over hard blocking
- Room placeholders or skeletons allowed while data loads

### Streaming State
- Current response source must be visible
- Office continues to show active execution while response streams

### Error State
- Distinguish between chat error, orchestration error, transport error, and rendering error
- Provide direct recovery actions

### Reconnect State
- Show non-blocking reconnect indicator
- Preserve last confirmed system state

## Accessibility
- Keyboard navigation across chat, tabs, overlays, and drawers
- Reduced motion mode must map to Simple Mode behavior
- Status must never rely only on color
- Major live changes require accessible announcements
- Tooltips and drawers need readable text equivalents

## Responsive Behavior
### Desktop
- Full three-zone layout

### Tablet
- Collapsible sidebar
- Bottom panel can become stacked drawer

### Mobile
- Chat-first view
- Office becomes secondary full-screen layer or tabbed view
- Essential controls remain reachable without hover

## Performance and Degradation Rules
- Office animation must degrade gracefully under lower-performance devices
- Live office rendering must never block message delivery or chat interaction
- When simulation rendering is constrained, the system must fall back to Executive Mode or Simple Mode without data loss

## UI Acceptance Criteria
- Users can clearly understand which agents are active and what they are doing
- A new request visibly enters the office workflow
- Collaboration, voting, hiring, and escalation are visually distinguishable
- The bottom panel gives deep operational insight without replacing the main office experience
- The interface remains readable and usable during long-running tasks
- Mobile and reduced-motion users still receive the full functional workflow
