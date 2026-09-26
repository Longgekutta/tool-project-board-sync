# CORE INVARIANTS: tool-project-board-sync

1. State Reconciliation Invariance:
   - Synchronization MUST be idempotent. Re-running sync with identical local tasks MUST NOT duplicate board items.

2. GraphQL Contract Invariance:
   - Generated GraphQL operations MUST target GitHub Projects v2 schema (`ProjectV2Item`, `addProjectV2ItemById`, `updateProjectV2ItemFieldValue`).

3. Hermetic Grace Invariance:
   - When offline or when GITHUB_TOKEN is omitted, the tool MUST gracefully operate in dry-run simulation mode without crashing.
