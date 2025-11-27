"""
Demo script showing multi-agent collaboration.

This script demonstrates how the multi-agent system works with
a manager coordinating research, analysis, and writing agents.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.manager.coordinator import ManagerAgent
from agents.research.gatherer import ResearchAgent
from agents.writer.creator import WriterAgent
from agents.analyzer.insights import AnalyzerAgent
from communication.message_bus import MessageBus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run the demo."""
    logger.info("=" * 60)
    logger.info("Multi-Agent System Demo")
    logger.info("=" * 60)

    # Create message bus
    message_bus = MessageBus()

    # Create agents
    logger.info("Initializing agents...")
    manager = ManagerAgent(message_bus)
    research_agent = ResearchAgent(message_bus)
    writer_agent = WriterAgent(message_bus)
    analyzer_agent = AnalyzerAgent(message_bus)

    # Start all agents
    logger.info("Starting agents...")
    await manager.start()
    await research_agent.start()
    await writer_agent.start()
    await analyzer_agent.start()

    logger.info(f"Active agents: {message_bus.get_registered_agents()}")

    try:
        # Example 1: Simple task delegation
        logger.info("\n" + "=" * 60)
        logger.info("Example 1: Research and Write Report")
        logger.info("=" * 60)

        result = await manager.delegate_task(
            description="Research and write a report on climate change",
            parameters={
                "topic": "climate change impacts",
                "needs_research": True
            }
        )

        logger.info("\nResult:")
        logger.info(json.dumps(result, indent=2, default=str))

        # Example 2: Direct agent interaction
        logger.info("\n" + "=" * 60)
        logger.info("Example 2: Direct Research Query")
        logger.info("=" * 60)

        research_task = {
            "task_id": "research_001",
            "description": "Research renewable energy",
            "parameters": {"query": "renewable energy trends"}
        }

        research_result = await research_agent.process_task(research_task)
        logger.info("\nResearch Result:")
        logger.info(json.dumps(research_result, indent=2, default=str))

        # Example 3: Analysis task
        logger.info("\n" + "=" * 60)
        logger.info("Example 3: Data Analysis")
        logger.info("=" * 60)

        analysis_task = {
            "task_id": "analysis_001",
            "description": "Analyze research data",
            "parameters": {"data": research_result}
        }

        analysis_result = await analyzer_agent.process_task(analysis_task)
        logger.info("\nAnalysis Result:")
        logger.info(json.dumps(analysis_result, indent=2, default=str))

        # Show message history
        logger.info("\n" + "=" * 60)
        logger.info("Message History Summary")
        logger.info("=" * 60)

        history = message_bus.get_history(limit=10)
        logger.info(f"Total messages: {len(message_bus.get_history())}")
        logger.info(f"Recent messages: {len(history)}")

        for msg in history[-5:]:
            logger.info(f"  {msg.from_} -> {msg.to}: {msg.message_type.value}")

    finally:
        # Stop all agents
        logger.info("\n" + "=" * 60)
        logger.info("Shutting down agents...")
        await manager.stop()
        await research_agent.stop()
        await writer_agent.stop()
        await analyzer_agent.stop()
        logger.info("Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
