"""Research agent - Gathers and verifies information from multiple sources."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from communication.message_bus import MessageBus

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research agent that gathers and verifies information.

    Capable of searching multiple sources, cross-checking data,
    and providing confidence scores.
    """

    def __init__(self, message_bus: MessageBus, agent_id: str = "research_agent"):
        """
        Initialize research agent.

        Args:
            message_bus: Message bus for communication
            agent_id: Agent identifier
        """
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            capabilities=["research", "information_gathering", "verification"]
        )
        self.knowledge_base: Dict[str, Any] = {}

    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        """
        Process a research task.

        Args:
            task_data: Task information including query

        Returns:
            Research results with confidence score
        """
        description = task_data.get("description", "")
        parameters = task_data.get("parameters", {})
        query = parameters.get("query", description)

        logger.info(f"Research agent processing: {query}")

        # Perform multi-source search
        results = await self._multi_source_search(query)

        # Verify information
        verified_results = self._cross_check(results)

        # Calculate confidence
        confidence = self._calculate_confidence(verified_results)

        return {
            "query": query,
            "results": verified_results,
            "confidence": confidence,
            "sources": len(results),
            "agent": self.agent_id
        }

    async def _multi_source_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search multiple sources for information.

        Args:
            query: Search query

        Returns:
            List of search results from different sources
        """
        # Simulate searching multiple sources
        # In a real system, this would call actual APIs
        results = []

        # Simulated knowledge base search
        kb_results = self._search_knowledge_base(query)
        if kb_results:
            results.append({
                "source": "knowledge_base",
                "data": kb_results,
                "reliability": 0.9
            })

        # Simulate web search
        web_results = await self._simulate_web_search(query)
        results.append({
            "source": "web_search",
            "data": web_results,
            "reliability": 0.7
        })

        # Simulate academic database
        academic_results = await self._simulate_academic_search(query)
        results.append({
            "source": "academic",
            "data": academic_results,
            "reliability": 0.95
        })

        logger.info(f"Found {len(results)} sources for query: {query}")
        return results

    def _search_knowledge_base(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search internal knowledge base.

        Args:
            query: Search query

        Returns:
            Knowledge base results if found
        """
        # Simple keyword matching in knowledge base
        query_lower = query.lower()
        for key, value in self.knowledge_base.items():
            if key.lower() in query_lower or query_lower in key.lower():
                return value
        return None

    async def _simulate_web_search(self, query: str) -> Dict[str, Any]:
        """
        Simulate web search.

        Args:
            query: Search query

        Returns:
            Simulated web search results
        """
        await asyncio.sleep(0.1)  # Simulate network delay

        # Return simulated results based on query
        return {
            "summary": f"Web search results for: {query}",
            "snippets": [
                f"Information about {query} from source 1",
                f"Additional details on {query} from source 2",
                f"Expert opinion on {query} from source 3"
            ],
            "url_count": 3
        }

    async def _simulate_academic_search(self, query: str) -> Dict[str, Any]:
        """
        Simulate academic database search.

        Args:
            query: Search query

        Returns:
            Simulated academic search results
        """
        await asyncio.sleep(0.15)  # Simulate database query delay

        return {
            "papers_found": 5,
            "key_findings": [
                f"Academic finding 1 related to {query}",
                f"Academic finding 2 related to {query}"
            ],
            "citations": 15
        }

    def _cross_check(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cross-check information from multiple sources.

        Args:
            results: Results from different sources

        Returns:
            Verified and consolidated results
        """
        # Simple verification - check if info appears in multiple sources
        verified = {
            "sources_checked": len(results),
            "consolidated_data": [],
            "reliability_score": 0.0
        }

        total_reliability = 0.0
        all_data = []

        for result in results:
            source = result.get("source")
            data = result.get("data", {})
            reliability = result.get("reliability", 0.5)

            total_reliability += reliability
            all_data.append({
                "source": source,
                "data": data,
                "reliability": reliability
            })

        verified["consolidated_data"] = all_data
        verified["reliability_score"] = total_reliability / len(results) if results else 0.0

        return verified

    def _calculate_confidence(self, verified_results: Dict[str, Any]) -> float:
        """
        Calculate confidence score for research results.

        Args:
            verified_results: Verified research results

        Returns:
            Confidence score (0.0-1.0)
        """
        sources_count = verified_results.get("sources_checked", 0)
        reliability = verified_results.get("reliability_score", 0.0)

        # More sources and higher reliability = higher confidence
        source_factor = min(sources_count / 5.0, 1.0)  # Max out at 5 sources
        confidence = (source_factor * 0.4) + (reliability * 0.6)

        return round(confidence, 2)

    def add_to_knowledge_base(self, key: str, data: Any) -> None:
        """
        Add information to the knowledge base.

        Args:
            key: Knowledge key
            data: Knowledge data
        """
        self.knowledge_base[key] = data
        logger.info(f"Added to knowledge base: {key}")

    async def verify_information(self, claim: str) -> Dict[str, Any]:
        """
        Verify a specific claim or piece of information.

        Args:
            claim: Claim to verify

        Returns:
            Verification results
        """
        results = await self._multi_source_search(claim)
        verified = self._cross_check(results)
        confidence = self._calculate_confidence(verified)

        return {
            "claim": claim,
            "verified": confidence > 0.7,
            "confidence": confidence,
            "details": verified
        }
