"""KEEP Phase 4.8 — Collaboration Task Dispatcher.

Coordinates subtask state machines, capability verification, dependency resolution,
and retry policies.

Specification: devdocs/p4/p4.8.txt
Owner: Member 2 (Communication & Task Dispatching)
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from backend.app.agents.collaboration.contracts import (
    CollaborationSecurityContext,
    CollaborationTask,
    TaskStatus,
)
from backend.app.agents.collaboration.repository import BaseCollaborationRepository
from backend.app.agents.errors import (
    CollaborationAgentCapabilityMismatchError,
    CollaborationAgentNotRegisteredError,
    CollaborationTaskDependencyFailedError,
    CollaborationTaskNotFoundError,
)
from backend.app.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)


class TaskDispatcher:
    """Manages task delegation, dependency gates, state transitions, and retries."""

    def __init__(
        self,
        repository: BaseCollaborationRepository,
        registry: AgentRegistry | None = None,
    ) -> None:
        self.repository = repository
        self.registry = registry

    async def get_task(
        self,
        task_id: str,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationTask:
        """Retrieves a task ensuring tenant boundary isolation."""
        task = await self.repository.get_task(task_id, security_context.tenant_id)
        if not task:
            raise CollaborationTaskNotFoundError(task_id)
        return task

    async def assign_task(
        self,
        task_id: str,
        agent_id: str,
        security_context: CollaborationSecurityContext,
        required_capability: str | None = None,
    ) -> CollaborationTask:
        """Assigns an agent to a task, validating registry presence and capabilities."""
        task = await self.get_task(task_id, security_context)

        # Validate agent if registry available
        if self.registry and agent_id not in ("coordinator", "reviewer", "critic", "synthesizer"):
            if not self.registry.is_registered(agent_id):
                raise CollaborationAgentNotRegisteredError(agent_id)
            if required_capability:
                metadata = self.registry.get_agent_metadata(agent_id)
                has_cap = any(c.capability == required_capability for c in metadata.capabilities)
                if not has_cap:
                    raise CollaborationAgentCapabilityMismatchError(agent_id, required_capability)

        task.agent_id = agent_id
        task.status = TaskStatus.ASSIGNED
        await self.repository.update_task(task)
        logger.info("Assigned task %s to agent %s in tenant %s.", task_id, agent_id, security_context.tenant_id)
        return task

    async def start_task(
        self,
        task_id: str,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationTask:
        """Starts task execution after validating dependency resolution and attempt limits."""
        task = await self.get_task(task_id, security_context)

        # Verify dependency resolution
        if task.dependencies:
            session_tasks = await self.repository.list_tasks(task.session_id, security_context.tenant_id)
            task_map = {t.task_id: t for t in session_tasks}

            failed_deps: list[str] = []
            unresolved_deps: list[str] = []

            for dep_id in task.dependencies:
                dep_task = task_map.get(dep_id)
                if not dep_task or dep_task.status in (TaskStatus.FAILED, TaskStatus.CANCELLED):
                    failed_deps.append(dep_id)
                elif dep_task.status != TaskStatus.SUCCEEDED:
                    unresolved_deps.append(dep_id)

            if failed_deps:
                task.status = TaskStatus.FAILED
                task.error_code = "COLLABORATION_TASK_DEPENDENCY_FAILED"
                task.completed_at = datetime.datetime.now(datetime.UTC)
                await self.repository.update_task(task)
                raise CollaborationTaskDependencyFailedError(task_id, failed_deps)

            if unresolved_deps:
                raise ValueError(f"Task '{task_id}' dependencies are not yet complete: {unresolved_deps}")

        # Check attempt limits
        task.attempt += 1
        if task.attempt > task.max_attempts:
            task.status = TaskStatus.FAILED
            task.error_code = "COLLABORATION_MAX_ATTEMPTS_EXCEEDED"
            task.completed_at = datetime.datetime.now(datetime.UTC)
            await self.repository.update_task(task)
            raise ValueError(f"Task '{task_id}' exceeded max execution attempts ({task.max_attempts}).")

        task.status = TaskStatus.RUNNING
        await self.repository.update_task(task)
        logger.info("Started task %s (attempt %d/%d).", task_id, task.attempt, task.max_attempts)
        return task

    async def complete_task(
        self,
        task_id: str,
        outputs: dict[str, Any],
        security_context: CollaborationSecurityContext,
    ) -> CollaborationTask:
        """Marks a task as successfully completed with produced output data."""
        task = await self.get_task(task_id, security_context)
        task.status = TaskStatus.SUCCEEDED
        task.outputs = outputs
        task.completed_at = datetime.datetime.now(datetime.UTC)
        await self.repository.update_task(task)
        logger.info("Task %s completed successfully.", task_id)
        return task

    async def fail_task(
        self,
        task_id: str,
        error_code: str,
        security_context: CollaborationSecurityContext,
        allow_retry: bool = True,
    ) -> CollaborationTask:
        """Handles task failure and determines whether to schedule retry or terminate."""
        task = await self.get_task(task_id, security_context)
        task.error_code = error_code

        if allow_retry and task.attempt < task.max_attempts:
            task.status = TaskStatus.PENDING
            logger.warning(
                "Task %s failed with %s; resetting to PENDING for retry (attempt %d/%d).",
                task_id,
                error_code,
                task.attempt,
                task.max_attempts,
            )
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.datetime.now(datetime.UTC)
            logger.error(
                "Task %s permanently failed with %s (attempts exhausted: %d/%d).",
                task_id,
                error_code,
                task.attempt,
                task.max_attempts,
            )

        await self.repository.update_task(task)
        return task

    async def get_ready_tasks(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
    ) -> list[CollaborationTask]:
        """Finds all pending tasks whose upstream dependencies have all succeeded."""
        session_tasks = await self.repository.list_tasks(session_id, security_context.tenant_id)
        task_map = {t.task_id: t for t in session_tasks}

        ready: list[CollaborationTask] = []
        for task in session_tasks:
            if task.status != TaskStatus.PENDING:
                continue
            all_deps_succeeded = True
            for dep_id in task.dependencies:
                dep_task = task_map.get(dep_id)
                if not dep_task or dep_task.status != TaskStatus.SUCCEEDED:
                    all_deps_succeeded = False
                    break
            if all_deps_succeeded:
                ready.append(task)

        return ready
