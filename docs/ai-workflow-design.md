# AI Workflow Design

This document describes how the platform's four layers interact at runtime to deliver end‑to‑end AI‑driven workflows.

---

## Conceptual Overview

```
  External World
       │  ▲
       ▼  │
┌──────────────────┐
│   integrations/  │  Adapters translate external protocols into internal events
└────────┬─────────┘
         │  events / data
         ▼
┌──────────────────┐
│    pipelines/    │  Orchestrator routes events to agent tasks; manages retries
└────────┬─────────┘
         │  task requests
         ▼
┌──────────────────┐
│     agents/      │  Agents reason, plan, and act; call algorithms as tools
└────────┬─────────┘
         │  algorithm calls
         ▼
┌──────────────────┐
│   algorithms/    │  Pure functions: search, optimise, classify, predict
└──────────────────┘
```

---

## Lifecycle of a Workflow

### 1. Trigger

A workflow begins when an **integration adapter** receives an external signal — an HTTP webhook, a scheduled cron tick, a message queue event, or a manual API call. The adapter normalises the signal into a typed `Event` and publishes it to the internal event bus.

### 2. Pipeline Dispatch

The **pipeline orchestrator** subscribes to the event bus. On receiving an `Event` it:
1. Looks up the matching pipeline definition.
2. Resolves the ordered list of pipeline steps.
3. Creates a `PipelineRun` record in the audit log.
4. Dispatches the first step as an `AgentTask`.

### 3. Agent Execution

An **agent** picks up the `AgentTask` and:
1. Loads its configuration and any required context from persistent state.
2. Invokes one or more **algorithm** functions to compute results (e.g., classify input, rank options, predict outcomes).
3. Decides on an action based on algorithm outputs and its own policy.
4. Executes the action (write data, call an integration, emit a new event).
5. Records the decision and outcome to the audit log.
6. Returns a `TaskResult` to the pipeline orchestrator.

### 4. Pipeline Continuation

The orchestrator receives the `TaskResult` and:
- If successful → advances to the next step or marks the run `COMPLETED`.
- If retryable failure → schedules a retry with exponential back‑off.
- If terminal failure → marks the run `FAILED` and triggers any configured alert integrations.

### 5. Response / Side Effects

Integration adapters may deliver results back to the external world (HTTP response, outbound webhook, database write) based on the final `PipelineRun` outcome.

---

## Agent Reasoning Loop

Agents that require multi‑step planning implement an internal **observe → orient → decide → act** (OODA) loop:

```
┌─────────────┐
│   Observe   │  Collect inputs: task payload, memory, sensor data
└──────┬──────┘
       ▼
┌─────────────┐
│   Orient    │  Run algorithms to understand the current situation
└──────┬──────┘
       ▼
┌─────────────┐
│   Decide    │  Select the best action from the policy
└──────┬──────┘
       ▼
┌─────────────┐
│    Act      │  Execute the action; emit events; update memory
└─────────────┘
       │
       └──► Loop back to Observe (for long‑running agents)
```

---

## State Management

| Scope | Storage | Owned by |
|---|---|---|
| Algorithm inputs/outputs | In‑memory only | `algorithms/` |
| Agent working memory | Short‑term key‑value store (e.g., Redis) | `agents/` |
| Agent long‑term memory | Vector or document store | `agents/` |
| Pipeline run state | Relational or document DB | `pipelines/` |
| Integration credentials | Secrets manager (never in code) | `integrations/` |

---

## Error Handling Strategy

1. **Algorithm errors** – propagated as typed exceptions; callers decide on retry.
2. **Agent errors** – caught by the pipeline; retried up to a configurable limit.
3. **Pipeline errors** – logged to the audit trail; operators are alerted.
4. **Integration errors** – isolated behind circuit‑breaker pattern; other integrations continue unaffected.

---

## Extending the Platform

To add a new workflow:

1. Implement or reuse an **algorithm** if new computation is required.
2. Create or extend an **agent** that calls the algorithm and encodes the decision policy.
3. Define a **pipeline** YAML that sequences agent tasks and wires up error handling.
4. Write or reuse an **integration adapter** if a new external system is involved.
5. Add tests at every layer and update this document to reflect the new workflow.
