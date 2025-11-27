"""Message definitions for agent communication."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class MessageType(Enum):
    """Types of messages that can be sent between agents."""

    TASK = "task"
    RESULT = "result"
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    STATUS = "status"
    ERROR = "error"


@dataclass
class Message:
    """
    Message structure for inter-agent communication.

    Attributes:
        to: Recipient agent ID
        from_: Sender agent ID
        message_type: Type of message
        content: Message payload
        correlation_id: ID for tracking related messages
        timestamp: When message was created
        metadata: Additional message metadata
    """

    to: str
    from_: str
    message_type: MessageType
    content: Any
    message_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def reply(self, content: Any, message_type: MessageType = MessageType.RESPONSE) -> "Message":
        """
        Create a reply message.

        Args:
            content: Reply content
            message_type: Type of reply message

        Returns:
            New message as a reply to this one
        """
        return Message(
            to=self.from_,
            from_=self.to,
            message_type=message_type,
            content=content,
            correlation_id=self.message_id
        )

    def __repr__(self) -> str:
        return (
            f"Message(id={self.message_id[:8]}..., "
            f"from={self.from_}, to={self.to}, "
            f"type={self.message_type.value})"
        )
