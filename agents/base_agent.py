"""
base_agent.py
~~~~~~~~~~~~~
Abstract base class for all Sovereign Architecture agents.

Every concrete agent must subclass ``BaseAgent`` and implement the ``run``
method.  The base class provides:

- A structured ``audit`` helper for writing tamper-evident decision records.
- A ``logger`` pre-configured with the agent's name.
- Enforcement of the agent ``MANIFEST`` contract at instantiation time.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Task:
    """A unit of work dispatched to an agent by the pipeline orchestrator."""

    task_id: str
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TaskResult:
    """The outcome produced by an agent after completing a task."""

    task_id: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AuditRecord:
    """An immutable record of a decision or action taken by an agent."""

    agent_name: str
    task_id: str
    action: str
    rationale: str
    outcome: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseAgent(ABC):
    """Abstract base class that all sovereign agents must implement.

    Subclasses must define a ``MANIFEST`` class attribute that declares the
    agent's identity and required permissions::

        MANIFEST = {
            "name": "MyAgent",
            "version": "1.0.0",
            "permissions": ["read:data", "write:results"],
        }
    """

    MANIFEST: dict[str, Any] = {}

    def __init__(self) -> None:
        self._validate_manifest()
        self.logger = logging.getLogger(self.MANIFEST["name"])
        self._audit_log: list[AuditRecord] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @abstractmethod
    def run(self, task: Task) -> TaskResult:
        """Execute *task* and return a :class:`TaskResult`.

        Implementations should:

        1. Observe relevant context from the task payload and memory.
        2. Call algorithm functions to orient and decide.
        3. Execute the chosen action.
        4. Record the decision via :meth:`audit`.
        5. Return a :class:`TaskResult` indicating success or failure.
        """

    # ------------------------------------------------------------------
    # Helpers available to subclasses
    # ------------------------------------------------------------------

    def audit(self, task_id: str, action: str, rationale: str, outcome: dict[str, Any]) -> None:
        """Append an immutable audit record for the given decision.

        Args:
            task_id:   Identifier of the task being processed.
            action:    A short description of the action taken.
            rationale: Human-readable explanation of why the action was chosen.
            outcome:   A dict capturing the result of the action.
        """
        record = AuditRecord(
            agent_name=self.MANIFEST["name"],
            task_id=task_id,
            action=action,
            rationale=rationale,
            outcome=outcome,
        )
        self._audit_log.append(record)
        self.logger.info(
            "audit",
            extra={
                "task_id": task_id,
                "action": action,
                "rationale": rationale,
                "outcome": outcome,
                "timestamp": record.timestamp.isoformat(),
            },
        )

    @property
    def audit_log(self) -> list[AuditRecord]:
        """Return a snapshot of this agent's audit records (read-only copy)."""
        return list(self._audit_log)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_manifest(self) -> None:
        required_keys = {"name", "version", "permissions"}
        missing = required_keys - self.MANIFEST.keys()
        if missing:
            raise ValueError(
                f"{self.__class__.__name__}.MANIFEST is missing required keys: {missing}"
            )
