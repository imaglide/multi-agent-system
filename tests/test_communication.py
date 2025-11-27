"""Tests for communication layer."""

import asyncio
import pytest

from communication.message import Message, MessageType
from communication.message_bus import MessageBus


@pytest.mark.asyncio
async def test_message_creation():
    """Test message creation and attributes."""
    msg = Message(
        to="agent_2",
        from_="agent_1",
        message_type=MessageType.TASK,
        content={"data": "test"}
    )

    assert msg.to == "agent_2"
    assert msg.from_ == "agent_1"
    assert msg.message_type == MessageType.TASK
    assert msg.content == {"data": "test"}
    assert msg.message_id is not None


@pytest.mark.asyncio
async def test_message_reply():
    """Test message reply functionality."""
    original = Message(
        to="agent_2",
        from_="agent_1",
        message_type=MessageType.TASK,
        content={"data": "test"}
    )

    reply = original.reply(content={"result": "done"})

    assert reply.to == "agent_1"
    assert reply.from_ == "agent_2"
    assert reply.correlation_id == original.message_id
    assert reply.content == {"result": "done"}


@pytest.mark.asyncio
async def test_message_bus_registration():
    """Test agent registration with message bus."""
    bus = MessageBus()
    inbox = asyncio.Queue()

    await bus.register_agent("agent_1", inbox)

    assert "agent_1" in bus.get_registered_agents()


@pytest.mark.asyncio
async def test_message_bus_send():
    """Test sending messages through message bus."""
    bus = MessageBus()
    inbox = asyncio.Queue()

    await bus.register_agent("agent_1", inbox)

    msg = Message(
        to="agent_1",
        from_="agent_2",
        message_type=MessageType.TASK,
        content={"task": "test"}
    )

    success = await bus.send_message(msg)
    assert success

    received = await inbox.get()
    assert received.to == "agent_1"
    assert received.content == {"task": "test"}


@pytest.mark.asyncio
async def test_message_bus_broadcast():
    """Test broadcasting messages."""
    bus = MessageBus()
    inbox1 = asyncio.Queue()
    inbox2 = asyncio.Queue()

    await bus.register_agent("agent_1", inbox1)
    await bus.register_agent("agent_2", inbox2)

    msg = Message(
        to="all",
        from_="manager",
        message_type=MessageType.BROADCAST,
        content={"announcement": "test"}
    )

    count = await bus.broadcast(msg)
    assert count == 2

    # Both agents should receive the message
    msg1 = await inbox1.get()
    msg2 = await inbox2.get()

    assert msg1.content == {"announcement": "test"}
    assert msg2.content == {"announcement": "test"}


@pytest.mark.asyncio
async def test_message_history():
    """Test message history tracking."""
    bus = MessageBus()
    inbox = asyncio.Queue()

    await bus.register_agent("agent_1", inbox)

    msg1 = Message(to="agent_1", from_="agent_2", message_type=MessageType.TASK, content={})
    msg2 = Message(to="agent_1", from_="agent_3", message_type=MessageType.TASK, content={})

    await bus.send_message(msg1)
    await bus.send_message(msg2)

    history = bus.get_history()
    assert len(history) == 2

    # Test filtering by agent
    agent2_history = bus.get_history(agent_id="agent_2")
    assert len(agent2_history) == 1
    assert agent2_history[0].from_ == "agent_2"


@pytest.mark.asyncio
async def test_message_bus_unregister():
    """Test agent unregistration."""
    bus = MessageBus()
    inbox = asyncio.Queue()

    await bus.register_agent("agent_1", inbox)
    assert "agent_1" in bus.get_registered_agents()

    await bus.unregister_agent("agent_1")
    assert "agent_1" not in bus.get_registered_agents()
