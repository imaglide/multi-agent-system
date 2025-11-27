"""Tests for multi-agent collaboration."""

import asyncio
import pytest

from agents.manager.coordinator import ManagerAgent
from agents.research.gatherer import ResearchAgent
from agents.writer.creator import WriterAgent
from agents.analyzer.insights import AnalyzerAgent
from communication.message_bus import MessageBus


@pytest.mark.asyncio
async def test_agent_lifecycle():
    """Test agent start and stop."""
    bus = MessageBus()
    agent = ResearchAgent(bus)

    await agent.start()
    assert agent.running
    assert agent.agent_id in bus.get_registered_agents()

    await agent.stop()
    assert not agent.running


@pytest.mark.asyncio
async def test_research_agent_task():
    """Test research agent processing."""
    bus = MessageBus()
    agent = ResearchAgent(bus)

    await agent.start()

    try:
        task_data = {
            "task_id": "test_001",
            "description": "Research artificial intelligence",
            "parameters": {"query": "artificial intelligence"}
        }

        result = await agent.process_task(task_data)

        assert "query" in result
        assert "results" in result
        assert "confidence" in result
        assert result["confidence"] >= 0.0
        assert result["confidence"] <= 1.0

    finally:
        await agent.stop()


@pytest.mark.asyncio
async def test_analyzer_agent_task():
    """Test analyzer agent processing."""
    bus = MessageBus()
    agent = AnalyzerAgent(bus)

    await agent.start()

    try:
        task_data = {
            "task_id": "test_002",
            "description": "Analyze data",
            "parameters": {
                "data": {
                    "values": [1, 2, 3, 4, 5],
                    "labels": ["a", "b", "c", "d", "e"]
                }
            }
        }

        result = await agent.process_task(task_data)

        assert "insights" in result
        assert "patterns" in result
        assert "statistics" in result
        assert len(result["insights"]) > 0

    finally:
        await agent.stop()


@pytest.mark.asyncio
async def test_writer_agent_task():
    """Test writer agent processing."""
    bus = MessageBus()
    writer = WriterAgent(bus)

    await writer.start()

    try:
        task_data = {
            "task_id": "test_003",
            "description": "Write article",
            "parameters": {
                "topic": "artificial intelligence",
                "content_type": "article",
                "style": "formal",
                "needs_research": False
            }
        }

        result = await writer.process_task(task_data)

        assert "content" in result
        assert "topic" in result
        assert "word_count" in result
        assert len(result["content"]) > 0

    finally:
        await writer.stop()


@pytest.mark.asyncio
async def test_manager_coordination():
    """Test manager coordinating multiple agents."""
    bus = MessageBus()

    manager = ManagerAgent(bus)
    research = ResearchAgent(bus)
    writer = WriterAgent(bus)
    analyzer = AnalyzerAgent(bus)

    # Start all agents
    await manager.start()
    await research.start()
    await writer.start()
    await analyzer.start()

    try:
        # Manager should decompose and delegate task
        result = await manager.delegate_task(
            description="Research and analyze climate change",
            parameters={"topic": "climate change"}
        )

        assert result is not None
        assert "subtask_count" in result or "status" in result

    finally:
        await manager.stop()
        await research.stop()
        await writer.stop()
        await analyzer.stop()


@pytest.mark.asyncio
async def test_agent_status():
    """Test agent status reporting."""
    bus = MessageBus()
    agent = ResearchAgent(bus)

    await agent.start()

    try:
        status = agent.get_status()

        assert status.agent_id == agent.agent_id
        assert status.state in ["idle", "busy"]
        assert isinstance(status.capabilities, list)
        assert status.workload >= 0.0

    finally:
        await agent.stop()


@pytest.mark.asyncio
async def test_multiple_concurrent_tasks():
    """Test handling multiple concurrent tasks."""
    bus = MessageBus()
    agent = ResearchAgent(bus)

    await agent.start()

    try:
        tasks = [
            {
                "task_id": f"test_{i}",
                "description": f"Research topic {i}",
                "parameters": {"query": f"topic {i}"}
            }
            for i in range(3)
        ]

        results = await asyncio.gather(
            *[agent.process_task(task) for task in tasks]
        )

        assert len(results) == 3
        for result in results:
            assert "query" in result
            assert "confidence" in result

    finally:
        await agent.stop()
