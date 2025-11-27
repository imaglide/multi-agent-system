"""Communication protocols for agent interactions."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class TaskStatus(Enum):
    """Status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(Enum):
    """Capabilities that agents can have."""

    RESEARCH = "research"
    WRITING = "writing"
    ANALYSIS = "analysis"
    COORDINATION = "coordination"
    DATA_PROCESSING = "data_processing"


@dataclass
class Task:
    """
    Task representation for agent processing.

    Attributes:
        task_id: Unique task identifier
        description: Task description
        task_type: Type of task
        parameters: Task-specific parameters
        priority: Task priority (0-10, higher is more urgent)
        required_capabilities: Capabilities needed to complete task
        status: Current task status
        result: Task result once completed
    """

    task_id: str
    description: str
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 5
    required_capabilities: Optional[list] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None

    def __post_init__(self):
        if self.required_capabilities is None:
            self.required_capabilities = []


@dataclass
class AgentStatus:
    """
    Agent status information.

    Attributes:
        agent_id: Agent identifier
        state: Current state (idle, busy, error)
        current_task: Currently processing task
        capabilities: Agent capabilities
        workload: Current workload (0.0-1.0)
    """

    agent_id: str
    state: str
    current_task: Optional[str] = None
    capabilities: list = None
    workload: float = 0.0

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class Protocol:
    """
    Communication protocol definitions.

    Defines standard message formats and interaction patterns.
    """

    @staticmethod
    def task_request(task: Task) -> Dict[str, Any]:
        """
        Create a task request payload.

        Args:
            task: Task to request

        Returns:
            Task request payload
        """
        return {
            "action": "task_request",
            "task": {
                "task_id": task.task_id,
                "description": task.description,
                "task_type": task.task_type,
                "parameters": task.parameters,
                "priority": task.priority,
                "required_capabilities": task.required_capabilities
            }
        }

    @staticmethod
    def task_response(task_id: str, result: Any, status: TaskStatus) -> Dict[str, Any]:
        """
        Create a task response payload.

        Args:
            task_id: Task identifier
            result: Task result
            status: Task status

        Returns:
            Task response payload
        """
        return {
            "action": "task_response",
            "task_id": task_id,
            "result": result,
            "status": status.value
        }

    @staticmethod
    def status_request() -> Dict[str, Any]:
        """
        Create a status request payload.

        Returns:
            Status request payload
        """
        return {"action": "status_request"}

    @staticmethod
    def status_response(agent_status: AgentStatus) -> Dict[str, Any]:
        """
        Create a status response payload.

        Args:
            agent_status: Agent status

        Returns:
            Status response payload
        """
        return {
            "action": "status_response",
            "agent_id": agent_status.agent_id,
            "state": agent_status.state,
            "current_task": agent_status.current_task,
            "capabilities": agent_status.capabilities,
            "workload": agent_status.workload
        }

    @staticmethod
    def data_request(query: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a data request payload.

        Args:
            query: Data query
            parameters: Additional parameters

        Returns:
            Data request payload
        """
        return {
            "action": "data_request",
            "query": query,
            "parameters": parameters or {}
        }

    @staticmethod
    def data_response(data: Any, confidence: float = 1.0) -> Dict[str, Any]:
        """
        Create a data response payload.

        Args:
            data: Response data
            confidence: Confidence score (0.0-1.0)

        Returns:
            Data response payload
        """
        return {
            "action": "data_response",
            "data": data,
            "confidence": confidence
        }
