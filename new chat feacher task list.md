# New Chat Feature Task List

Use this file as the execution tracker. Mark tasks only when the code, tests, and review for that item are complete.

## Planning and Requirements
- [x] Audit the current chat implementation across frontend and backend.
- [x] Create the execution plan document.
- [x] Write the product requirements in `new chat feacher.md`.
- [x] Write the detailed UI/UX specification in `new chat feacher ui ux.md`.
- [x] Approve final scope, acceptance criteria, and rollout boundaries.

## Architecture and Data Design
- [x] Define chat domain entities: conversation, message, feedback, participant, session metadata.
- [x] Choose the production persistence model for chat data.
- [x] Design database schema and write migrations.
- [x] Define canonical HTTP API contracts.
- [x] Define canonical real-time event contracts.
- [x] Document error states, retries, and idempotency rules.

## Backend Implementation
- [x] Replace file-based chat storage in `dcis/backend/src/infrastructure/repositories/chat_repository.py`.
- [x] Implement a real chat repository with persistence guarantees.
- [x] Build session lifecycle services: create, list, load, rename/title, delete.
- [x] Build message lifecycle services: send, stream, persist, replay, paginate.
- [x] Integrate real agent routing and system prompt resolution.
- [x] Integrate conversation context and memory services.
- [x] Add feedback persistence and feedback APIs.
- [x] Add validation, rate limiting, logging, and metrics.
- [x] Add canonical workspace projection APIs for rooms, activity feed, stats, task stages, and replay.
- [x] Remove mock or temporary chat behavior from the shipping path.
- [x] Persist real orchestration events for replay, room timelines, and graph overlays.
- [x] Add dedicated APIs for voting, hiring, collaboration logs, and memory-vault inspection.

## Frontend Implementation
- [x] Design the new chat state model and transport layer.
- [x] Refactor or replace `dcis/frontend/src/components/chat/ChatInterface.tsx`.
- [x] Refactor or replace `dcis/frontend/src/components/chat/ChatHistorySidebar.tsx`.
- [x] Align frontend session state with backend-generated session identifiers.
- [x] Implement message streaming and delivery-state reconciliation.
- [x] Implement composer UX, keyboard behavior, and accessibility rules.
- [x] Implement feedback interactions and backend sync.
- [x] Implement empty, loading, reconnect, retry, and error states.
- [x] Bind the office workspace UI to canonical backend workspace data.
- [x] Apply final approved UI/UX from the design spec.
- [x] Implement room-specific drill-down panels for Strategy Center, Boss's Office, Voting Chamber, Collaboration Hub, Specialist Incubator, Memory Vault, and Active Pods.
- [x] Implement a real interactive DAG viewer and replay controls backed by persisted workspace events.

## Testing and Quality
- [x] Rewrite backend tests for the new repository and service contracts.
- [x] Add API integration tests for sessions, messages, streaming, and feedback.
- [x] Rewrite frontend unit tests around the new chat state and components.
- [x] Rewrite Playwright flows to validate the real chat journey.
- [x] Validate long-session behavior, multi-message continuity, and deletion flows.
- [x] Run performance, observability, and failure-mode checks.

## Release Readiness
- [x] Review data migration or cutover needs for existing chat history.
- [x] Validate environment variables, secrets, and deployment dependencies.
- [x] Perform final manual QA against the integrated stack.
- [x] Confirm all acceptance criteria are met.
- [x] Mark the feature release-ready.
