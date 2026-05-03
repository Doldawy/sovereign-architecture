# Agents

This directory contains the autonomous AI agent definitions for the Sovereign Architecture platform.

## What is an Agent?

An agent is a self‑contained unit of autonomous behaviour. Each agent:

- Receives a **task** from the pipeline orchestrator.
- Reads relevant **context** from its memory stores.
- Invokes **algorithm** functions to reason about the task.
- Selects and executes an **action**.
- Records the decision and outcome to the **audit log**.

## Directory Structure

```
agents/
├── README.md          ← this file
└── base_agent.py      ← abstract base class all agents must implement
```

Add new agent implementations alongside `base_agent.py`, one module per agent type.

## Implementing a New Agent

1. Create a new file, e.g. `agents/my_agent.py`.
2. Subclass `BaseAgent` from `base_agent.py`.
3. Implement the `run(task)` method with your agent's logic.
4. Declare required permissions in the agent's `MANIFEST` dict.
5. Register the agent in the pipeline configuration.

## Guidelines

- Agents must be stateless between tasks; persist any required state to the designated memory stores.
- All algorithm calls must go through `algorithms/` — agents must not embed raw computation.
- Every action taken must be recorded via `self.audit(...)`.
- Keep each agent focused on a single responsibility; compose complex workflows in `pipelines/`.

## Testing

Place agent unit tests in `agents/tests/`. Mock algorithm calls and audit sinks to keep tests fast and deterministic.
