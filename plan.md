# Autonomous Athlete Performance Planner - Implementation Plan

## Phase 1: Project Setup & Data Simulation
- [ ] Initialize the project repository (Python Backend, Capacitor/Web Frontend).
- [ ] Set up SQLite Database and define schemas (Athlete Profile, Workload, Recovery, Events).
- [ ] Build a Mock API/Service to generate synthetic GPS, workload, and wellness data.
- [ ] Implement a Mock Calendar Service for upcoming match schedules.
**Checkpoint:** The mock services can reliably generate consistent data and be queried via API endpoints. The process iterates until the synthetic data accurately reflects realistic athlete metrics without throwing errors.

## Phase 2: Load-Management Algorithm & Constraints
- [ ] Define the core load-management algorithm incorporating ACWR and custom hard rules.
- [ ] Implement scheduling logic to assign rest, light training, or heavy training days.
- [ ] Implement verification logic to ensure workload constraints (e.g., fatigue thresholds) are never breached.
- [ ] Write unit tests for the algorithm ensuring it properly flags constraint violations.
**Checkpoint:** The algorithm can take a state (fatigue + upcoming match) and successfully output a valid 7-day training plan. Iterates until constraints are strictly mathematically enforced.

## Phase 3: Autonomous Agent Architecture (Groq Integration)
- [ ] Integrate the Groq API to power the core agent reasoning.
- [ ] Build the "Onboarding Agent" (Grill mode) to interview the user and populate initial stats.
- [ ] Build the "Planner Agent" that ingests daily simulated data, evaluates the current plan, and recalculates when necessary.
- [ ] Implement the trigger mechanism to force at least 2 meaningful plan revisions based on simulated fatigue/schedule changes.
- [ ] Ensure agent logic aligns with the strict medical guardrails (no medical/injury claims).
**Checkpoint:** The agent can autonomously evaluate a shift in wellness data, output a revised plan twice, and successfully verify it against the Phase 2 constraints. Iterates until reasoning and guardrails are flawlessly maintained.

## Phase 4: Web UI (Neumorphic Design) & Capacitor Integration
- [ ] Set up the frontend framework optimized for Capacitor deployment.
- [ ] Implement the Neumorphic design system (soft shadows, low contrast borders, matching background/element colors).
- [ ] Build the Dashboard View with "Enter Manually" and "Pull from Device" workflows.
- [ ] Build the Event Tracker and Daily Schedule views.
- [ ] Build the Persistent Chat interface that hovers across all pages for direct agent interaction.
- [ ] Integrate click-to-edit interactions to trigger specific planners.
**Checkpoint:** The Web UI matches the exact Neumorphic aesthetic, handles responsive routing, and successfully communicates with the Python APIs. Iterates until visual constraints and UX flows are perfect.

## Phase 5: Integration & Verification
- [ ] Connect the Web UI to the backend Agent logic and Data simulators.
- [ ] Implement end-to-end testing of the onboarding "grilling" flow.
- [ ] Test the daily update flow: UI shows new synthetic data -> Agent reacts -> Dashboard updates.
- [ ] Final validation against the problem statement requirements (showing 2 revisions, constraint checking).
**Checkpoint:** Complete E2E system run without errors. Iterates until the demonstration seamlessly satisfies the problem statement.
