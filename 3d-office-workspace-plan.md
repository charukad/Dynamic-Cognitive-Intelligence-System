# 3D Office Workspace Plan

## Goal
Replace the 2D "Interactive Office Workspace" experience with a production-grade 3D office visualization that shows:
- Room topology and live room state.
- Agent bodies and current work assignment.
- Active task/events mapped to the room where work is happening.

## Delivery Phases

### Phase 1: 3D Foundation (Completed)
- [x] Add `Office3DWorkspace` using React Three Fiber + Drei.
- [x] Render room pods as real 3D objects with status-driven color/emissive state.
- [x] Render agent bodies with live status and active-task labels.
- [x] Render task pulses from timeline events.
- [x] Keep room selection and room-detail workflows fully functional.
- [x] Keep 2D fallback for non-3D/test environments.

### Phase 2: Production UX and Data Fidelity
- [ ] Replace procedural room geometry with optimized GLB assets.
- [ ] Add real route-line animation between active rooms.
- [ ] Add event playback mode synchronized with replay frames.
- [ ] Add accessibility mirror controls for all 3D interactions.
- [ ] Add panel for filtering agent/task layers.

### Phase 3: Enterprise Hardening
- [ ] Performance budget: FPS floor, draw-call budget, memory budget.
- [ ] LOD and quality auto-scaling for low-end devices.
- [ ] Error/fallback path when WebGL context is unavailable.
- [ ] Telemetry for scene interaction and load timings.
- [ ] E2E and visual regression coverage for 3D states.

## Implementation Standards
- Keep 3D scene deterministic from workspace API state.
- Preserve existing backend contract; no mock-only data paths.
- Ensure every 3D interaction has an accessible 2D control equivalent.
- Maintain graceful degradation (`Simple`/`Executive` fallback).

## Current Status
Phase 1 is integrated and running in `Full Simulation` mode.
