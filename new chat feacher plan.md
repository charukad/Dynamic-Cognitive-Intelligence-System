# New Chat Feature Execution Plan

## Purpose
Deliver the chat system as a primary product capability with production-grade architecture, real persistence, real agent execution, and a maintainable frontend/backend contract. This plan assumes the final feature must not ship with mock responses, JSON-file chat storage, or temporary fallback behavior.

## Current Audit Summary
- The primary specification files, `new chat feacher.md` and `new chat feacher ui ux.md`, are now populated and treated as the approved scope baseline for implementation and release review.
- The current frontend chat experience already exists in `dcis/frontend/src/components/chat`, but it mixes local state, `localStorage`, direct fetches, and a WebSocket fallback path.
- The current backend chat stack uses file-based session storage in `dcis/backend/src/infrastructure/repositories/chat_repository.py`, which is not suitable for enterprise-grade durability, concurrency, or auditability.
- The UI expects richer behavior than the backend guarantees today. There is no hardened contract for session lifecycle, streaming, feedback, retries, or message status reconciliation.

## Delivery Principles
- No mock or simulated chat behavior in the shipped path.
- Persist chat data in a real datastore with explicit schema and migrations.
- Define one canonical chat API contract for HTTP and real-time events.
- Keep message history, agent routing, feedback, and analytics consistent across backend and frontend.
- Build with observability, validation, error handling, and test coverage from the start.

## Target Solution
### Backend
- Create a dedicated chat domain for conversations, messages, feedback, participants, and session metadata.
- Replace JSON-file persistence with a real repository backed by the project’s production datastore strategy.
- Add explicit APIs for session create/list/read/update/delete, message send/list, feedback submit, and title generation.
- Standardize streaming over one supported protocol and document event payloads.
- Route messages through the real orchestration and LLM stack, with agent-aware system prompts and session context.
- Add audit logging, rate limiting, validation, and operational metrics.

### Frontend
- Refactor chat into a state-driven architecture with clear separation between transport, store, and presentation.
- Build a reliable session sidebar, message timeline, composer, streaming state, retry/error UX, and feedback interactions.
- Remove fragile local-only session handling and align state with backend-generated identifiers and metadata.
- Implement the new UI/UX only after the missing spec file is populated and approved.

## Execution Phases
### Phase 0: Requirements Lock
- Fill both empty source documents with business scope, UX flows, edge cases, and acceptance criteria.
- Confirm whether chat is single-agent, multi-agent, or orchestrated by the meta-orchestrator.
- Confirm persistence, auth, analytics, and retention requirements.

### Phase 1: Architecture and Data Model
- Define conversation and message schemas.
- Choose the production persistence path and write migrations.
- Define API contracts and real-time event envelopes.
- Document delivery semantics for retries, failures, and idempotent message submission.

## Error States, Retries, and Idempotency Rules
- Session bootstrap failures must surface as recoverable UI errors with explicit retry actions and no hidden fallback session creation.
- Message send failures must preserve the failed user turn in the timeline with retry controls; retries create a new delivery attempt but keep the original user-visible content.
- Realtime transport failure must degrade to HTTP send without losing the active session or selected agent context.
- Backend `POST /chat/sessions/{session_id}/messages/send` must treat the client-provided message `id` as the idempotency key for the user turn within that session.
- Duplicate user message IDs in the same session must not create duplicate user messages; the existing persisted turn should be reused and the assistant delivery should reconcile onto that canonical turn.
- Assistant streaming is not independently idempotent; if generation fails after the user turn is persisted, the assistant message must be marked `failed` and surfaced for explicit user retry.
- Feedback submission is idempotent at the `(session_id, message_id)` level. Re-submitting feedback replaces the prior value rather than creating duplicates.
- Session deletion is terminal for the canonical record. The UI must remove the deleted session, clear associated local state, and open or create the next valid session.
- All retryable failures must emit structured logs and metrics with the route name, session ID, retry eligibility, and failure category.

### Phase 2: Backend Foundation
- Implement repositories, services, and API routes.
- Integrate session memory, feedback capture, and agent routing.
- Add tests for schema, persistence, services, and API contracts.

### Phase 3: Frontend Rebuild
- Replace ad hoc chat state with a structured client data layer.
- Rebuild the chat page, sidebar, composer, and feedback flow against the new contracts.
- Add loading, reconnect, retry, empty, and failure states.

### Phase 4: Integration Hardening
- Run end-to-end flows against real backend services.
- Validate streaming, session switching, deletion, and long conversations.
- Add telemetry, performance checks, and production-readiness review.

## Key Risks
- Requirements are undefined until the two spec files are populated.
- Current chat behavior is split across HTTP and WebSocket paths with inconsistent assumptions.
- Migrating from file storage to a real datastore requires a clean cutover strategy.
- Existing tests appear to assume simplified or simulated chat behavior and will need rewriting.

## Definition of Done
- Approved requirements exist in both source spec files.
- Chat sessions and messages use real persistent storage and migrations.
- Frontend and backend use one documented contract for session and message flows.
- Streaming and feedback work against the real agent stack.
- Unit, integration, and E2E tests pass for the new chat system.
- No shipping code depends on mock chat responses, temporary storage, or placeholder UX.
