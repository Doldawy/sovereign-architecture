"""
pipeline.py
~~~~~~~~~~~
Pipeline data models and runner for the Sovereign Architecture platform.

A :class:`Pipeline` is an ordered collection of :class:`PipelineStep` objects.
The :class:`PipelineRunner` executes them in dependency order, handles retries,
and records every run to an audit log.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class PipelineStep:
    """A single step in a pipeline.

    Args:
        name:            Unique name for this step within the pipeline.
        handler:         Callable that executes the step logic.  Receives the
                         accumulated *context* dict and returns a dict of
                         outputs that will be merged into the context.
        depends_on:      Names of steps that must succeed before this step runs.
        timeout_seconds: Maximum seconds the handler may run (informational for
                         now; enforcement can be added via threading/asyncio).
        retries:         Number of times to retry on failure before giving up.
    """

    name: str
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    depends_on: list[str] = field(default_factory=list)
    timeout_seconds: int = 60
    retries: int = 0


@dataclass
class StepRun:
    """Runtime record for a single step execution attempt."""

    step_name: str
    status: StepStatus = StepStatus.PENDING
    attempt: int = 0
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass
class PipelineRun:
    """Runtime record for a complete pipeline execution."""

    pipeline_name: str
    run_id: str
    status: RunStatus = RunStatus.PENDING
    step_runs: list[StepRun] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass
class Pipeline:
    """A named, versioned sequence of :class:`PipelineStep` objects."""

    name: str
    version: str
    steps: list[PipelineStep] = field(default_factory=list)
    description: str = ""


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class PipelineRunner:
    """Executes a :class:`Pipeline`, managing step ordering and retries.

    Usage::

        runner = PipelineRunner()
        run = runner.execute(pipeline, initial_context={"input": data})
    """

    def execute(
        self,
        pipeline: Pipeline,
        run_id: str | None = None,
        initial_context: dict[str, Any] | None = None,
    ) -> PipelineRun:
        """Run *pipeline* and return the completed :class:`PipelineRun`.

        Args:
            pipeline:        The pipeline to execute.
            run_id:          Optional identifier for this run (auto-generated if omitted).
            initial_context: Seed data available to the first step.

        Returns:
            A :class:`PipelineRun` reflecting the final status of every step.
        """
        if run_id is None:
            run_id = f"{pipeline.name}-{int(time.time())}"

        run = PipelineRun(
            pipeline_name=pipeline.name,
            run_id=run_id,
            status=RunStatus.RUNNING,
            context=dict(initial_context or {}),
            started_at=datetime.now(timezone.utc),
        )
        logger.info("pipeline.started", extra={"run_id": run_id, "pipeline": pipeline.name})

        completed: set[str] = set()
        failed: set[str] = set()

        for step in self._ordered_steps(pipeline):
            step_run = self._execute_step(step, run.context, completed, failed)
            run.step_runs.append(step_run)
            if step_run.status == StepStatus.SUCCEEDED:
                completed.add(step.name)
                run.context.update(step_run.output)
            else:
                failed.add(step.name)

        run.status = RunStatus.COMPLETED if not failed else RunStatus.FAILED
        run.finished_at = datetime.now(timezone.utc)
        logger.info(
            "pipeline.finished",
            extra={"run_id": run_id, "status": run.status, "failed_steps": list(failed)},
        )
        return run

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ordered_steps(self, pipeline: Pipeline) -> list[PipelineStep]:
        """Return steps in topological order respecting ``depends_on``."""
        ordered: list[PipelineStep] = []
        remaining = list(pipeline.steps)
        resolved: set[str] = set()

        while remaining:
            progress = False
            for step in list(remaining):
                if all(dep in resolved for dep in step.depends_on):
                    ordered.append(step)
                    resolved.add(step.name)
                    remaining.remove(step)
                    progress = True
            if not progress:
                unresolved = [s.name for s in remaining]
                raise ValueError(f"Circular or unresolvable dependencies: {unresolved}")

        return ordered

    def _execute_step(
        self,
        step: PipelineStep,
        context: dict[str, Any],
        completed: set[str],
        failed: set[str],
    ) -> StepRun:
        """Run *step*, retrying up to ``step.retries`` times on failure."""
        # Skip if any dependency failed
        if any(dep in failed for dep in step.depends_on):
            logger.warning("step.skipped", extra={"step": step.name, "reason": "dependency_failed"})
            return StepRun(step_name=step.name, status=StepStatus.SKIPPED)

        step_run = StepRun(step_name=step.name, started_at=datetime.now(timezone.utc))
        attempts = step.retries + 1

        for attempt in range(1, attempts + 1):
            step_run.attempt = attempt
            step_run.status = StepStatus.RUNNING
            logger.info("step.started", extra={"step": step.name, "attempt": attempt})
            try:
                output = step.handler(dict(context))
                step_run.output = output or {}
                step_run.status = StepStatus.SUCCEEDED
                step_run.finished_at = datetime.now(timezone.utc)
                logger.info("step.succeeded", extra={"step": step.name, "attempt": attempt})
                return step_run
            except Exception as exc:  # noqa: BLE001
                step_run.error = str(exc)
                logger.warning(
                    "step.failed",
                    extra={"step": step.name, "attempt": attempt, "error": str(exc)},
                )

        step_run.status = StepStatus.FAILED
        step_run.finished_at = datetime.now(timezone.utc)
        return step_run
