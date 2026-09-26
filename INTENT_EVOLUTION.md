# INTENT EVOLUTION: tool-project-board-sync

## Initial State
- Agentic execution progresses locally, but cloud GitHub Projects v2 Kanban remains empty or stagnant, isolating human project managers.

## Transduced Invariants
1. Bidirectional mapping between local task manifests (JSON / Markdown) and GitHub Projects v2 items.
2. Structured GraphQL v4 mutations with batch reconciliation.
3. Offline simulation mode guaranteeing zero test network dependence.
