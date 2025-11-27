"""Manager agent - Coordinates and delegates tasks to specialist agents."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from agents.base_agent import BaseAgent
from communication.message import Message, MessageType
from communication.message_bus import MessageBus
from communication.protocol import AgentCapability, Task, TaskStatus

logger = logging.getLogger(__name__)


class ManagerAgent(BaseAgent):
    """
    Manager agent that orchestrates task delegation.

    Breaks down complex tasks into subtasks and assigns them
    to appropriate specialist agents.
    """

    def __init__(self, message_bus: MessageBus, agent_id: str = "manager"):
        """
        Initialize manager agent.

        Args:
            message_bus: Message bus for communication
            agent_id: Agent identifier
        """
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            capabilities=["coordination", "task_decomposition", "synthesis"]
        )
        self.pending_results: Dict[str, List[Message]] = {}
        self.subtask_mapping: Dict[str, str] = {}  # subtask_id -> parent_task_id

    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        """
        Process a task by delegating to specialists.

        Args:
            task_data: Task information

        Returns:
            Synthesized result from all subtasks
        """
        task_id = task_data.get("task_id", str(uuid4()))
        description = task_data.get("description", "")
        parameters = task_data.get("parameters", {})

        logger.info(f"Manager processing task: {description}")

        # Decompose task into subtasks
        subtasks = self._decompose(description, parameters)
        logger.info(f"Decomposed into {len(subtasks)} subtasks")

        # Assign subtasks to appropriate agents
        subtask_ids = []
        for subtask in subtasks:
            agent_id = self._select_agent(subtask)
            subtask_id = str(uuid4())

            subtask_message = {
                "task_id": subtask_id,
                "description": subtask["description"],
                "task_type": subtask["type"],
                "parameters": subtask.get("parameters", {})
            }

            await self.send_message(agent_id, subtask_message, MessageType.TASK)
            subtask_ids.append(subtask_id)
            self.subtask_mapping[subtask_id] = task_id

        # Gather results from all subtasks
        results = await self._gather_results(subtask_ids, timeout=60.0)

        # Synthesize final output
        final_result = self._synthesize(results)

        return final_result

    def _decompose(self, description: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Break down a complex task into subtasks.

        Args:
            description: Task description
            parameters: Task parameters

        Returns:
            List of subtasks
        """
        # Simple task decomposition logic
        # In a real system, this would use more sophisticated logic or LLM
        subtasks = []

        # Check if this is a research-heavy task
        if any(keyword in description.lower() for keyword in ["research", "gather", "find", "investigate"]):
            subtasks.append({
                "type": "research",
                "description": f"Research: {description}",
                "parameters": parameters
            })

        # Check if analysis is needed
        if any(keyword in description.lower() for keyword in ["analyze", "insights", "trends", "patterns"]):
            subtasks.append({
                "type": "analysis",
                "description": f"Analyze data for: {description}",
                "parameters": parameters
            })

        # Check if content creation is needed
        if any(keyword in description.lower() for keyword in ["write", "create", "report", "document"]):
            subtasks.append({
                "type": "writing",
                "description": f"Write content for: {description}",
                "parameters": parameters
            })

        # If no specific keywords, create a general subtask
        if not subtasks:
            subtasks.append({
                "type": "general",
                "description": description,
                "parameters": parameters
            })

        return subtasks

    def _select_agent(self, subtask: Dict[str, Any]) -> str:
        """
        Select the best agent for a subtask.

        Args:
            subtask: Subtask information

        Returns:
            Agent ID
        """
        task_type = subtask["type"]

        agent_mapping = {
            "research": "research_agent",
            "analysis": "analyzer_agent",
            "writing": "writer_agent",
            "general": "research_agent"  # Default to research
        }

        return agent_mapping.get(task_type, "research_agent")

    async def _gather_results(self, subtask_ids: List[str], timeout: float = 60.0) -> Dict[str, Any]:
        """
        Gather results from multiple subtasks.

        Args:
            subtask_ids: List of subtask IDs to wait for
            timeout: Timeout in seconds

        Returns:
            Dictionary of subtask results
        """
        results = {}
        start_time = asyncio.get_event_loop().time()
        remaining = set(subtask_ids)

        while remaining and (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                # Check inbox for results
                if not self.inbox.empty():
                    message = await asyncio.wait_for(self.inbox.get(), timeout=0.5)

                    if message.message_type == MessageType.RESULT:
                        task_id = message.content.get("task_id")
                        if task_id in remaining:
                            results[task_id] = message.content.get("result")
                            remaining.remove(task_id)
                            logger.info(f"Received result for subtask {task_id}")

                await asyncio.sleep(0.1)
            except asyncio.TimeoutError:
                continue

        if remaining:
            logger.warning(f"Timed out waiting for subtasks: {remaining}")

        return results

    def _synthesize(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize results from multiple subtasks.

        Args:
            results: Dictionary of subtask results

        Returns:
            Synthesized final result
        """
        # Simple synthesis - in a real system, this would be more sophisticated
        synthesized = {
            "summary": "Task completed with multiple subtask results",
            "subtask_count": len(results),
            "subtask_results": results,
            "status": "completed"
        }

        # Try to identify research, analysis, and writing components
        research_data = []
        analysis_data = []
        written_content = []

        for task_id, result in results.items():
            if isinstance(result, dict):
                if "research" in str(result).lower():
                    research_data.append(result)
                elif "analysis" in str(result).lower() or "insights" in str(result).lower():
                    analysis_data.append(result)
                elif "content" in str(result).lower():
                    written_content.append(result)

        if research_data:
            synthesized["research"] = research_data
        if analysis_data:
            synthesized["analysis"] = analysis_data
        if written_content:
            synthesized["content"] = written_content

        return synthesized

    async def delegate_task(
        self,
        description: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        High-level method to delegate a task.

        Args:
            description: Task description
            parameters: Task parameters

        Returns:
            Task result
        """
        task_data = {
            "task_id": str(uuid4()),
            "description": description,
            "parameters": parameters or {}
        }

        return await self.process_task(task_data)
