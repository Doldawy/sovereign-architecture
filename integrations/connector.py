"""
connector.py
~~~~~~~~~~~~
Base interface for all Sovereign Architecture integration connectors.

Every adapter that connects the platform to an external service must subclass
:class:`BaseConnector` and implement :meth:`send` (for outbound calls) and,
if the adapter is also an inbound source, :meth:`receive`.

The base class provides:

- A :attr:`logger` pre-configured with the connector's name.
- A :meth:`health_check` hook for liveness probes.
- A structured :meth:`emit_event` helper for publishing normalised events to
  the internal event bus.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Event model
# ---------------------------------------------------------------------------


@dataclass
class Event:
    """A normalised internal event produced by an inbound connector.

    Args:
        source:     Name of the connector that produced the event.
        event_type: Dot-separated event type string, e.g. ``"data.received"``.
        payload:    Arbitrary event data.
        event_id:   Optional unique identifier for deduplication.
        occurred_at: When the event occurred (defaults to now).
    """

    source: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Base connector
# ---------------------------------------------------------------------------


class BaseConnector(ABC):
    """Abstract base class for all integration connectors.

    Subclasses must define a ``NAME`` class attribute identifying the
    external service::

        class SlackConnector(BaseConnector):
            NAME = "slack"
            ...
    """

    NAME: str = ""

    def __init__(self) -> None:
        if not self.NAME:
            raise ValueError(
                f"{self.__class__.__name__} must define a non-empty NAME class attribute."
            )
        self.logger = logging.getLogger(f"integrations.{self.NAME}")

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send *payload* to the external service.

        Args:
            payload: Data to transmit.  Must not contain raw credentials.

        Returns:
            A dict describing the service's response (status, ids, etc.).

        Raises:
            ConnectorError: If the external service returns an error or is
                            unreachable.
        """

    # ------------------------------------------------------------------
    # Optional override
    # ------------------------------------------------------------------

    def receive(self, raw_event: dict[str, Any]) -> Event:
        """Normalise a raw inbound event from the external service.

        Override this method in connectors that act as event sources.
        The default implementation wraps the raw event with minimal metadata.

        Args:
            raw_event: The raw data received from the external service.

        Returns:
            A normalised :class:`Event` ready for publication to the event bus.
        """
        return Event(
            source=self.NAME,
            event_type="raw.received",
            payload=raw_event,
        )

    def health_check(self) -> bool:
        """Return ``True`` if the external service is reachable.

        Override in concrete connectors to perform an actual liveness probe.
        The default implementation always returns ``True``.
        """
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def emit_event(self, event: Event, bus: Any | None = None) -> None:
        """Log and optionally publish *event* to the internal event bus.

        Args:
            event: The normalised event to emit.
            bus:   Optional event bus instance.  If provided, ``bus.publish``
                   is called with the event.
        """
        self.logger.info(
            "event.emitted",
            extra={
                "source": event.source,
                "event_type": event.event_type,
                "event_id": event.event_id,
                "occurred_at": event.occurred_at.isoformat(),
            },
        )
        if bus is not None:
            bus.publish(event)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ConnectorError(Exception):
    """Raised when a connector cannot complete an outbound call."""

    def __init__(self, connector_name: str, message: str) -> None:
        super().__init__(f"[{connector_name}] {message}")
        self.connector_name = connector_name
