# New Chat Feature Specification

## Feature Name
Neural Link Living Office Platform

## Purpose
Build the chat system into the primary interaction layer of DCIS and express it as a Living AI Organization Interface. The feature must support real conversations with specialized agents, durable conversation history, session continuity, visible orchestration, feedback capture, and production-grade reliability. The shipping implementation must not depend on mock responses, JSON-file persistence, or temporary local-only behavior.

## Product Goals
- Make chat the fastest path to use DCIS capabilities.
- Support long-running, persistent conversations with agents.
- Preserve context across sessions using real backend-managed conversation state.
- Make the internal orchestration process visible through a real-time office simulation.
- Collect structured user feedback on agent responses for quality improvement.
- Provide a frontend and backend contract that is stable enough for future extensions.

## Primary User Outcomes
- A user can start a new conversation from anywhere in the app.
- A user can choose a specific agent or use orchestrated routing when enabled.
- A user can send prompts and receive streamed responses with clear delivery states.
- A user can watch the request move through planners, specialists, collaboration rooms, and governance flows.
- A user can reopen older conversations and continue them with full history.
- A user can rename, review, delete, and organize conversations.
- A user can rate responses using thumbs up or thumbs down, with optional detailed feedback.

## In Scope
- Conversation lifecycle: create, load, list, continue, rename, archive or delete.
- Message lifecycle: send, stream, persist, replay, retry, and reconcile status.
- Agent-aware chat: explicit agent selection for each conversation.
- Visual Office Mode: real-time workspace showing strategy, collaboration, governance, hiring, memory, and execution areas.
- Session metadata: title, timestamps, agent context, last activity, message count.
- Persistent feedback capture tied to conversation, message, and agent.
- Live office overlays: activity feed, active employees, office stats, and task graph visibility.
- Reliable empty, loading, streaming, error, reconnect, and retry states.
- Backend observability for chat requests, failures, latency, and usage.

## Out of Scope for Initial Delivery
- Multi-user collaborative chat editing.
- Voice-first chat flows.
- File attachment workflows inside chat.
- Public sharing of conversations.
- Offline-first sync.
- Full 3D free-roam environment.

## Business Requirements
### Conversation Management
- The system must create a backend-managed conversation identifier before durable messaging begins.
- The user must be able to create a new chat without losing previous conversations.
- The conversation list must be ordered by recent activity.
- The system must generate a default title from the first user message, with later manual rename support.
- The user must be able to delete a conversation with confirmation.

### Messaging
- The user must be able to send multi-line prompts.
- The UI must support streamed assistant output.
- The system must preserve message order and final message state.
- The system must support retrying a failed send without duplicating persisted messages.
- Each message must carry a stable backend identifier.

### Agent Interaction
- A conversation must have a selected agent context.
- The system must expose the available agents from the backend, not hard-coded frontend state.
- Agent metadata shown in the UI must come from the agent API.
- The response path must use real agent prompts and real model execution.

### Visual Office Mode
- The main workspace must represent agents as active employees in a living office.
- Distinct rooms must represent planning, orchestration, collaboration, voting, hiring, memory, and specialized execution.
- Agent proximity, movement, and room occupancy must reflect real runtime state rather than decorative animation.
- Users must be able to click rooms, agents, and task overlays to inspect internal system behavior.

### Transparency and Operations
- The system must expose a live activity feed for major orchestration events.
- The system must expose an active employee roster with operational status.
- The system must expose office-level stats such as cost, success rate, retry count, and confidence indicators.
- Replay or step-through inspection must be supported in the product direction, even if implemented after the initial chat delivery.

### Feedback and Quality
- Feedback must be stored against the exact response message.
- The user must be able to submit thumbs up or thumbs down from the chat timeline.
- Detailed feedback must be supported by API contract even if the first UI release only exposes quick reactions.
- Feedback submission must not block normal chat usage.

### Persistence and Data
- Chat sessions and messages must be stored in a real persistent datastore with schema and migration support.
- Chat history must not depend on local JSON files or browser-only storage.
- Local browser state may be used only as a cache, never as the source of truth.
- The backend must support pagination for large histories.

### Reliability and Security
- Chat APIs must validate payloads and reject malformed requests.
- Real-time transport must support reconnect and recovery behavior.
- The system must log failures and expose metrics for latency, message volume, and error rate.
- The implementation must support future authentication and user scoping even if the current project is not fully auth-enabled.

## Functional Requirements
### FR-1 Session Lifecycle
- Create conversation
- List conversations
- Load conversation history
- Rename conversation
- Delete conversation
- Return session metadata in every relevant response

### FR-2 Message Lifecycle
- Submit message
- Receive streamed or chunked response
- Persist user and agent messages
- Retry failed message
- Expose message status values such as `queued`, `streaming`, `completed`, and `failed`

### FR-3 Feedback Lifecycle
- Submit thumbs up or thumbs down
- Prevent duplicate conflicting feedback for the same message without explicit update
- Return stored feedback state so the UI can render it accurately after reload

### FR-4 Agent Discovery
- List available agents with id, name, description, status, and execution metadata needed by the UI

### FR-5 Observability
- Track session counts, message counts, per-agent response latency, feedback volume, and failure rates

### FR-6 Office Simulation Lifecycle
- Render room-level office state for active workflows
- Show request path from chat intake to execution and back to final response
- Represent collaboration, voting, hiring, escalation, and retry events visually
- Provide inspection panels for rooms, agents, and task flow

## Non-Functional Requirements
- Use production persistence with migrations and concurrency safety.
- Preserve chronological ordering under concurrent writes.
- Handle long conversations without loading the entire history by default.
- Keep contracts versioned and documented.
- Degrade gracefully between Simple, Executive, and Full Simulation modes based on capability and user preference.
- Maintain automated coverage at unit, integration, and end-to-end levels.

## Recommended Technical Direction
- Use backend-managed conversation and message identifiers.
- Use one canonical chat contract shared by HTTP and real-time transport.
- Persist conversations, messages, and feedback in the project’s production datastore path rather than file storage.
- Keep the frontend chat client state normalized by conversation id and message id.
- Support optimistic UI only when it can be reconciled safely with backend results.

## API Capability Expectations
- `POST /chat/sessions`
- `GET /chat/sessions`
- `GET /chat/sessions/{session_id}`
- `PATCH /chat/sessions/{session_id}`
- `DELETE /chat/sessions/{session_id}`
- `POST /chat/sessions/{session_id}/messages`
- `GET /chat/sessions/{session_id}/messages`
- `POST /chat/feedback`

Exact route naming can change during architecture work, but the capability set is required.

## Acceptance Criteria
- A user can create, continue, rename, and delete chats from the UI.
- A user can send a message and receive a real agent response with visible progress state.
- Refreshing the page preserves chat history from the backend.
- Feedback survives reload and is tied to the correct message.
- No shipping path depends on `localStorage` as the source of truth or JSON files under `backend/data/chat_sessions`.
- Backend, frontend, and E2E tests cover the core chat journey.
