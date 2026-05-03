# Integrations

This directory contains the integration layer for the Sovereign Architecture platform — adapters that connect the platform to external services, APIs, and data sources.

## What is an Integration?

An integration adapter:

- **Inbound** – translates external signals (webhooks, queue messages, scheduled ticks) into typed internal `Event` objects and publishes them to the event bus.
- **Outbound** – receives instructions from pipelines or agents and calls the corresponding external API or service.

## Directory Structure

```
integrations/
├── README.md          ← this file
└── connector.py       ← BaseConnector interface all adapters must implement
```

Add new adapter implementations alongside `connector.py`, one module per external system.

## Implementing a New Connector

1. Create a new file, e.g. `integrations/slack_connector.py`.
2. Subclass `BaseConnector` from `connector.py`.
3. Implement `send(payload)` for outbound calls.
4. Implement `receive(raw_event) -> Event` for inbound normalisation (if applicable).
5. Store credentials as environment variables or via the secrets manager — **never** hard‑code them.

## Security Guidelines

- All credentials are injected at runtime from a secrets manager.
- Connectors must validate and sanitise all data received from external sources before forwarding it internally.
- Implement a **circuit‑breaker** to prevent cascading failures when an external service is degraded.
- Log every outbound call and inbound event (excluding sensitive payloads) for auditability.

## Testing

Place connector unit tests in `integrations/tests/`. Use HTTP mocking libraries to simulate external service responses without real network calls.
