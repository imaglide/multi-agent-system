"""Message bus for routing messages between agents."""

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set

from .message import Message, MessageType

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Central message routing and delivery system.

    Manages message queues for all agents and handles routing,
    broadcasting, and communication logging.
    """

    def __init__(self):
        """Initialize the message bus."""
        self.agents: Dict[str, asyncio.Queue] = {}
        self.message_history: List[Message] = []
        self.running = False
        self._lock = asyncio.Lock()

    async def register_agent(self, agent_id: str, inbox: asyncio.Queue) -> None:
        """
        Register an agent with the message bus.

        Args:
            agent_id: Unique identifier for the agent
            inbox: Agent's inbox queue for receiving messages
        """
        async with self._lock:
            if agent_id in self.agents:
                logger.warning(f"Agent {agent_id} already registered, updating inbox")
            self.agents[agent_id] = inbox
            logger.info(f"Registered agent: {agent_id}")

    async def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an agent from the message bus.

        Args:
            agent_id: Agent to unregister
        """
        async with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                logger.info(f"Unregistered agent: {agent_id}")

    async def send_message(self, message: Message) -> bool:
        """
        Send a message to a specific agent.

        Args:
            message: Message to send

        Returns:
            True if message was delivered, False otherwise
        """
        async with self._lock:
            if message.to not in self.agents:
                logger.error(f"Agent {message.to} not found")
                return False

            inbox = self.agents[message.to]
            await inbox.put(message)
            self.message_history.append(message)

            logger.debug(
                f"Message sent: {message.from_} -> {message.to} "
                f"({message.message_type.value})"
            )
            return True

    async def broadcast(self, message: Message, exclude: Optional[Set[str]] = None) -> int:
        """
        Broadcast a message to all agents.

        Args:
            message: Message to broadcast
            exclude: Set of agent IDs to exclude from broadcast

        Returns:
            Number of agents that received the message
        """
        exclude = exclude or set()
        count = 0

        async with self._lock:
            for agent_id, inbox in self.agents.items():
                if agent_id not in exclude and agent_id != message.from_:
                    broadcast_msg = Message(
                        to=agent_id,
                        from_=message.from_,
                        message_type=MessageType.BROADCAST,
                        content=message.content,
                        metadata=message.metadata
                    )
                    await inbox.put(broadcast_msg)
                    count += 1

            self.message_history.append(message)
            logger.debug(f"Broadcast from {message.from_} to {count} agents")

        return count

    def get_history(
        self,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get message history.

        Args:
            agent_id: Filter by agent ID (sender or receiver)
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        history = self.message_history

        if agent_id:
            history = [
                msg for msg in history
                if msg.from_ == agent_id or msg.to == agent_id
            ]

        if limit:
            history = history[-limit:]

        return history

    def get_registered_agents(self) -> List[str]:
        """
        Get list of registered agent IDs.

        Returns:
            List of agent IDs
        """
        return list(self.agents.keys())

    async def wait_for_message(
        self,
        agent_id: str,
        correlation_id: Optional[str] = None,
        timeout: float = 30.0
    ) -> Optional[Message]:
        """
        Wait for a specific message.

        Args:
            agent_id: Agent to wait for message from
            correlation_id: Correlation ID to match
            timeout: Timeout in seconds

        Returns:
            Message if received, None if timeout
        """
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            for msg in reversed(self.message_history):
                if msg.from_ == agent_id:
                    if correlation_id is None or msg.correlation_id == correlation_id:
                        return msg
            await asyncio.sleep(0.1)

        return None

    def clear_history(self) -> None:
        """Clear message history."""
        self.message_history.clear()
        logger.info("Message history cleared")
