# Orchestration

The Orchestration subsystem coordinates collection across WizardOps.

It is responsible for:

- Building collection jobs
- Executing collectors
- Reporting progress
- Handling failures

It is **not** responsible for:

- Inspecting the operating system
- Discovering machine capabilities
- Reading logs directly
- Parsing events

Those responsibilities belong to Inventory, Collectors, and Events.

## Execution Flow

Inventory
    ↓
Orchestration
    ↓
Collectors
    ↓
Archive
