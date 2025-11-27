"""Writer agent - Creates structured content based on research and analysis."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from agents.base_agent import BaseAgent
from communication.message import MessageType
from communication.message_bus import MessageBus

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """
    Writer agent that creates structured content.

    Capable of generating various content types, requesting research,
    and adapting to different writing styles.
    """

    def __init__(self, message_bus: MessageBus, agent_id: str = "writer_agent"):
        """
        Initialize writer agent.

        Args:
            message_bus: Message bus for communication
            agent_id: Agent identifier
        """
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            capabilities=["writing", "content_creation", "summarization", "structuring"]
        )
        self.content_cache: Dict[str, Any] = {}

    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        """
        Process a writing task.

        Args:
            task_data: Task information including topic and style

        Returns:
            Generated content
        """
        description = task_data.get("description", "")
        parameters = task_data.get("parameters", {})

        topic = parameters.get("topic", description)
        style = parameters.get("style", "formal")
        content_type = parameters.get("content_type", "article")
        needs_research = parameters.get("needs_research", True)

        logger.info(f"Writer agent creating {content_type} on: {topic}")

        # Request research if needed
        research_data = None
        if needs_research:
            research_data = await self._request_research(topic)

        # Request analysis if available
        analysis_data = None
        if research_data and parameters.get("needs_analysis", False):
            analysis_data = await self._request_analysis(research_data)

        # Generate content
        content = await self._generate(
            topic=topic,
            style=style,
            content_type=content_type,
            research_data=research_data,
            analysis_data=analysis_data
        )

        return {
            "content": content,
            "topic": topic,
            "content_type": content_type,
            "style": style,
            "word_count": len(content.split()),
            "agent": self.agent_id
        }

    async def _request_research(self, topic: str) -> Optional[Dict[str, Any]]:
        """
        Request research data from research agent.

        Args:
            topic: Research topic

        Returns:
            Research results
        """
        request_id = str(uuid4())
        logger.info(f"Requesting research on: {topic}")

        message_content = {
            "task_id": request_id,
            "description": f"Research: {topic}",
            "parameters": {"query": topic}
        }

        await self.send_message("research_agent", message_content, MessageType.TASK)

        # Wait for response
        response = await self._wait_for_response(request_id, timeout=10.0)

        if response:
            logger.info("Received research data")
            return response.content.get("result")

        logger.warning("No research data received")
        return None

    async def _request_analysis(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Request analysis from analyzer agent.

        Args:
            data: Data to analyze

        Returns:
            Analysis results
        """
        request_id = str(uuid4())
        logger.info("Requesting data analysis")

        message_content = {
            "task_id": request_id,
            "description": "Analyze research data",
            "parameters": {"data": data}
        }

        await self.send_message("analyzer_agent", message_content, MessageType.TASK)

        # Wait for response
        response = await self._wait_for_response(request_id, timeout=10.0)

        if response:
            logger.info("Received analysis data")
            return response.content.get("result")

        logger.warning("No analysis data received")
        return None

    async def _wait_for_response(self, request_id: str, timeout: float) -> Optional[Any]:
        """
        Wait for a response message.

        Args:
            request_id: Request ID to wait for
            timeout: Timeout in seconds

        Returns:
            Response message or None
        """
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            if not self.inbox.empty():
                message = await asyncio.wait_for(self.inbox.get(), timeout=0.5)
                if message.message_type == MessageType.RESULT:
                    if message.content.get("task_id") == request_id:
                        return message
                else:
                    # Put it back if it's not what we're looking for
                    await self.inbox.put(message)

            await asyncio.sleep(0.1)

        return None

    async def _generate(
        self,
        topic: str,
        style: str,
        content_type: str,
        research_data: Optional[Dict[str, Any]] = None,
        analysis_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate content.

        Args:
            topic: Content topic
            style: Writing style
            content_type: Type of content
            research_data: Research results
            analysis_data: Analysis results

        Returns:
            Generated content
        """
        await asyncio.sleep(0.2)  # Simulate generation time

        # Build content based on available data
        sections = []

        # Introduction
        sections.append(self._generate_introduction(topic, style))

        # Research-based content
        if research_data:
            sections.append(self._generate_research_section(research_data))

        # Analysis-based content
        if analysis_data:
            sections.append(self._generate_analysis_section(analysis_data))

        # Conclusion
        sections.append(self._generate_conclusion(topic, style))

        content = "\n\n".join(sections)
        return content

    def _generate_introduction(self, topic: str, style: str) -> str:
        """Generate introduction section."""
        if style == "formal":
            return f"# {topic}\n\nThis document provides a comprehensive overview of {topic}. The following sections explore key aspects, research findings, and analytical insights."
        elif style == "casual":
            return f"# {topic}\n\nLet's dive into {topic}! We'll explore what makes this interesting and what we've learned."
        else:
            return f"# {topic}\n\nAn exploration of {topic} and its implications."

    def _generate_research_section(self, research_data: Dict[str, Any]) -> str:
        """Generate section based on research data."""
        section = "## Research Findings\n\n"

        results = research_data.get("results", {})
        confidence = research_data.get("confidence", 0.0)

        consolidated = results.get("consolidated_data", [])

        if consolidated:
            section += "Based on multiple sources, the following information was gathered:\n\n"
            for i, source_data in enumerate(consolidated, 1):
                source = source_data.get("source", "unknown")
                section += f"- Source {i} ({source}): {source_data.get('data', {}).get('summary', 'Data available')}\n"

        section += f"\n*Research confidence: {confidence * 100:.0f}%*"

        return section

    def _generate_analysis_section(self, analysis_data: Dict[str, Any]) -> str:
        """Generate section based on analysis data."""
        section = "## Analysis & Insights\n\n"

        insights = analysis_data.get("insights", [])
        if insights:
            section += "Key insights from the analysis:\n\n"
            for insight in insights:
                section += f"- {insight}\n"
        else:
            section += "Analytical processing reveals important patterns and trends in the data."

        return section

    def _generate_conclusion(self, topic: str, style: str) -> str:
        """Generate conclusion section."""
        if style == "formal":
            return f"## Conclusion\n\nIn summary, this analysis of {topic} provides valuable insights supported by research and data analysis. The findings contribute to our understanding and inform future directions."
        elif style == "casual":
            return f"## Wrapping Up\n\nThat's our look at {topic}! We've covered the key points and what they mean."
        else:
            return f"## Conclusion\n\nThis overview of {topic} synthesizes research and analysis to provide a comprehensive perspective."

    async def create_content(
        self,
        topic: str,
        content_type: str = "article",
        style: str = "formal"
    ) -> str:
        """
        High-level method to create content.

        Args:
            topic: Content topic
            content_type: Type of content
            style: Writing style

        Returns:
            Generated content
        """
        task_data = {
            "task_id": str(uuid4()),
            "description": f"Write {content_type} on {topic}",
            "parameters": {
                "topic": topic,
                "content_type": content_type,
                "style": style
            }
        }

        result = await self.process_task(task_data)
        return result.get("content", "")
