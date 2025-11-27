"""Base agent class for all agent implementations."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from communication.message import Message, MessageType
from communication.message_bus import MessageBus
from communication.protocol import AgentStatus, Protocol, Task

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Provides core functionality for message handling, task processing,
    and lifecycle management.
    """

    def __init__(
        self,
        agent_id: str,
        message_bus: MessageBus,
        capabilities: Optional[List[str]] = None
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Unique identifier for this agent
            message_bus: Message bus for communication
            capabilities: List of agent capabilities
        """
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.capabilities = capabilities or []

        self.inbox = asyncio.Queue()
        self.state = "idle"
        self.current_task: Optional[str] = None
        self.running = False
        self._process_task: Optional[asyncio.Task] = None

        logger.info(f"Initialized {self.__class__.__name__} with ID: {agent_id}")

    async def start(self) -> None:
        """Start the agent."""
        await self.message_bus.register_agent(self.agent_id, self.inbox)
        self.running = True
        self._process_task = asyncio.create_task(self._process_messages())
        logger.info(f"Agent {self.agent_id} started")

    async def stop(self) -> None:
        """Stop the agent."""
        self.running = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        await self.message_bus.unregister_agent(self.agent_id)
        logger.info(f"Agent {self.agent_id} stopped")

    async def _process_messages(self) -> None:
        """Process incoming messages from inbox."""
        while self.running:
            try:
                message = await asyncio.wait_for(self.inbox.get(), timeout=0.5)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message in {self.agent_id}: {e}")

    async def _handle_message(self, message: Message) -> None:
        """
        Handle an incoming message.

        Args:
            message: Incoming message
        """
        logger.debug(f"{self.agent_id} received {message.message_type.value} from {message.from_}")

        try:
            if message.message_type == MessageType.TASK:
                await self._handle_task_message(message)
            elif message.message_type == MessageType.REQUEST:
                await self._handle_request_message(message)
            elif message.message_type == MessageType.STATUS:
                await self._handle_status_message(message)
            elif message.message_type == MessageType.BROADCAST:
                await self._handle_broadcast_message(message)
            else:
                await self.handle_message(message)
        except Exception as e:
            logger.error(f"Error handling message in {self.agent_id}: {e}")
            await self._send_error(message, str(e))

    async def _handle_task_message(self, message: Message) -> None:
        """Handle task assignment message."""
        self.state = "busy"
        task_data = message.content
        self.current_task = task_data.get("task_id")

        try:
            result = await self.process_task(task_data)

            response = Message(
                to=message.from_,
                from_=self.agent_id,
                message_type=MessageType.RESULT,
                content={
                    "task_id": task_data.get("task_id"),
                    "result": result,
                    "status": "completed"
                },
                correlation_id=message.message_id
            )
            await self.message_bus.send_message(response)

        except Exception as e:
            logger.error(f"Task processing error in {self.agent_id}: {e}")
            await self._send_error(message, str(e))
        finally:
            self.state = "idle"
            self.current_task = None

    async def _handle_request_message(self, message: Message) -> None:
        """Handle generic request message."""
        content = message.content
        action = content.get("action")

        if action == "status":
            status = self.get_status()
            response = Message(
                to=message.from_,
                from_=self.agent_id,
                message_type=MessageType.STATUS,
                content={
                    "state": status.state,
                    "current_task": status.current_task,
                    "capabilities": status.capabilities,
                    "workload": status.workload
                },
                correlation_id=message.message_id
            )
            await self.message_bus.send_message(response)
        else:
            # Pass to subclass
            await self.handle_message(message)

    async def _handle_status_message(self, message: Message) -> None:
        """Handle status update message."""
        await self.handle_message(message)

    async def _handle_broadcast_message(self, message: Message) -> None:
        """Handle broadcast message."""
        await self.handle_message(message)

    async def _send_error(self, original_message: Message, error: str) -> None:
        """Send error response."""
        error_message = Message(
            to=original_message.from_,
            from_=self.agent_id,
            message_type=MessageType.ERROR,
            content={"error": error, "original_message_id": original_message.message_id},
            correlation_id=original_message.message_id
        )
        await self.message_bus.send_message(error_message)

    async def send_message(
        self,
        to: str,
        content: Any,
        message_type: MessageType = MessageType.REQUEST
    ) -> bool:
        """
        Send a message to another agent.

        Args:
            to: Recipient agent ID
            content: Message content
            message_type: Type of message

        Returns:
            True if sent successfully
        """
        message = Message(
            to=to,
            from_=self.agent_id,
            message_type=message_type,
            content=content
        )
        return await self.message_bus.send_message(message)

    def get_status(self) -> AgentStatus:
        """
        Get current agent status.

        Returns:
            Agent status
        """
        return AgentStatus(
            agent_id=self.agent_id,
            state=self.state,
            current_task=self.current_task,
            capabilities=self.capabilities,
            workload=0.5 if self.state == "busy" else 0.0
        )

    @abstractmethod
    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        """
        Process a task. Must be implemented by subclasses.

        Args:
            task_data: Task data to process

        Returns:
            Task result
        """
        pass

    async def handle_message(self, message: Message) -> None:
        """
        Handle custom message types. Override in subclasses.

        Args:
            message: Message to handle
        """
        logger.debug(f"{self.agent_id} ignoring message type: {message.message_type}")
