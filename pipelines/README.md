# Pipelines

This directory contains automation pipeline definitions and the pipeline runner for the Sovereign Architecture platform.

## What is a Pipeline?

A pipeline is an ordered sequence of agent tasks that together accomplish a higher‑level goal. Pipelines:

- Are triggered by **events** published by integration adapters.
- Dispatch **tasks** to agents in the configured order.
- Handle **retries**, **timeouts**, and **failure routing**.
- Record every run to the **audit log**.

## Directory Structure

```
pipelines/
├── README.md          ← this file
└── pipeline.py        ← Pipeline and PipelineStep data classes + runner
```

Add YAML pipeline definitions (e.g. `pipelines/definitions/my_pipeline.yaml`) alongside `pipeline.py`.

## Defining a Pipeline

Pipelines are described in YAML:

```yaml
# pipelines/definitions/example.yaml
name: example-pipeline
version: "1.0"
trigger:
  type: event
  event_name: data.received
steps:
  - name: validate
    agent: ValidationAgent
    timeout_seconds: 30
    retries: 3
  - name: process
    agent: ProcessingAgent
    timeout_seconds: 120
    retries: 1
    depends_on: [validate]
on_failure:
  alert: ops-channel
```

## Guidelines

- Every step must be **idempotent** — safe to re‑run after a failure.
- Steps should have explicit `timeout_seconds` and `retries` values.
- Use `depends_on` to express ordering; the runner will parallelise independent steps.
- Do not embed business logic inside the pipeline YAML; delegate all logic to agents.

## Testing

Place pipeline integration tests in `pipelines/tests/`. Use the `PipelineRunner` with mock agents to validate step sequencing and error‑handling behaviour.
