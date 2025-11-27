"""Coordination utilities for multi-agent orchestration."""

import asyncio
import logging
from typing import Dict, List, Optional, Set

from .message import Message, MessageType
from .message_bus import MessageBus
from .protocol import AgentStatus, Task, TaskStatus

logger = logging.getLogger(__name__)


class Coordinator:
    """
    Coordinates multiple agents working on related tasks.

    Manages task distribution, result aggregation, and agent synchronization.
    """

    def __init__(self, message_bus: MessageBus):
        """
        Initialize coordinator.

        Args:
            message_bus: Message bus for communication
        """
        self.message_bus = message_bus
        self.active_tasks: Dict[str, Task] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        self.agent_status: Dict[str, AgentStatus] = {}

    async def assign_task(
        self,
        task: Task,
        agent_id: str,
        from_agent: str = "coordinator"
    ) -> bool:
        """
        Assign a task to a specific agent.

        Args:
            task: Task to assign
            agent_id: Target agent ID
            from_agent: Assigning agent ID

        Returns:
            True if task was assigned successfully
        """
        message = Message(
            to=agent_id,
            from_=from_agent,
            message_type=MessageType.TASK,
            content={
                "task_id": task.task_id,
                "description": task.description,
                "task_type": task.task_type,
                "parameters": task.parameters
            }
        )

        success = await self.message_bus.send_message(message)

        if success:
            self.active_tasks[task.task_id] = task
            self.task_assignments[task.task_id] = agent_id
            task.status = TaskStatus.IN_PROGRESS
            logger.info(f"Assigned task {task.task_id} to {agent_id}")

        return success

    async def wait_for_results(
        self,
        task_ids: List[str],
        timeout: float = 60.0
    ) -> Dict[str, any]:
        """
        Wait for multiple tasks to complete.

        Args:
            task_ids: List of task IDs to wait for
            timeout: Timeout in seconds

        Returns:
            Dictionary of task_id -> result
        """
        results = {}
        start_time = asyncio.get_event_loop().time()
        remaining_tasks = set(task_ids)

        while remaining_tasks and (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check message history for results
            for task_id in list(remaining_tasks):
                if task_id in self.active_tasks:
                    task = self.active_tasks[task_id]
                    agent_id = self.task_assignments.get(task_id)

                    if agent_id:
                        # Look for response from agent
                        msg = await self.message_bus.wait_for_message(
                            agent_id,
                            correlation_id=None,
                            timeout=0.5
                        )

                        if msg and msg.message_type == MessageType.RESULT:
                            content = msg.content
                            if content.get("task_id") == task_id:
                                results[task_id] = content.get("result")
                                task.result = content.get("result")
                                task.status = TaskStatus.COMPLETED
                                remaining_tasks.remove(task_id)
                                logger.info(f"Received result for task {task_id}")

            await asyncio.sleep(0.1)

        # Mark timed out tasks as failed
        for task_id in remaining_tasks:
            if task_id in self.active_tasks:
                self.active_tasks[task_id].status = TaskStatus.FAILED
                logger.warning(f"Task {task_id} timed out")

        return results

    async def gather_agent_status(self, agent_ids: Optional[List[str]] = None) -> Dict[str, AgentStatus]:
        """
        Gather status from multiple agents.

        Args:
            agent_ids: List of agent IDs (None for all registered agents)

        Returns:
            Dictionary of agent_id -> status
        """
        if agent_ids is None:
            agent_ids = self.message_bus.get_registered_agents()

        status_dict = {}

        for agent_id in agent_ids:
            message = Message(
                to=agent_id,
                from_="coordinator",
                message_type=MessageType.REQUEST,
                content={"action": "status"}
            )

            await self.message_bus.send_message(message)

        # Wait for responses
        await asyncio.sleep(0.5)

        # Collect status responses
        for agent_id in agent_ids:
            msg = await self.message_bus.wait_for_message(agent_id, timeout=1.0)
            if msg and msg.message_type == MessageType.STATUS:
                status = AgentStatus(
                    agent_id=agent_id,
                    state=msg.content.get("state", "unknown"),
                    current_task=msg.content.get("current_task"),
                    capabilities=msg.content.get("capabilities", []),
                    workload=msg.content.get("workload", 0.0)
                )
                status_dict[agent_id] = status
                self.agent_status[agent_id] = status

        return status_dict

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get status of a specific task.

        Args:
            task_id: Task ID

        Returns:
            Task status or None if not found
        """
        task = self.active_tasks.get(task_id)
        return task.status if task else None

    def get_active_tasks(self) -> List[Task]:
        """
        Get all active tasks.

        Returns:
            List of active tasks
        """
        return [
            task for task in self.active_tasks.values()
            if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
        ]

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task to cancel

        Returns:
            True if cancelled successfully
        """
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            logger.info(f"Cancelled task {task_id}")
            return True
        return False
