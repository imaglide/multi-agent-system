"""Communication infrastructure for multi-agent system."""

from .message import Message, MessageType
from .message_bus import MessageBus
from .protocol import Protocol
from .coordination import Coordinator

__all__ = ["Message", "MessageType", "MessageBus", "Protocol", "Coordinator"]
