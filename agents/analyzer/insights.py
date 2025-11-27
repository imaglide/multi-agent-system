"""Analyzer agent - Extracts insights and patterns from data."""

import asyncio
import logging
from collections import Counter
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from communication.message_bus import MessageBus

logger = logging.getLogger(__name__)


class AnalyzerAgent(BaseAgent):
    """
    Analyzer agent that extracts insights from data.

    Capable of pattern detection, trend analysis, statistical processing,
    and generating visualizations.
    """

    def __init__(self, message_bus: MessageBus, agent_id: str = "analyzer_agent"):
        """
        Initialize analyzer agent.

        Args:
            message_bus: Message bus for communication
            agent_id: Agent identifier
        """
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            capabilities=["analysis", "pattern_detection", "statistics", "visualization"]
        )
        self.analysis_history: List[Dict[str, Any]] = []

    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        """
        Process an analysis task.

        Args:
            task_data: Task information including data to analyze

        Returns:
            Analysis results with insights
        """
        description = task_data.get("description", "")
        parameters = task_data.get("parameters", {})
        data = parameters.get("data", {})

        logger.info(f"Analyzer agent processing: {description}")

        # Extract insights
        insights = self._extract_insights(data)

        # Detect patterns
        patterns = self._detect_patterns(data)

        # Generate statistics
        statistics = self._generate_statistics(data)

        # Create visualization metadata
        visualizations = self._create_visualizations(insights, patterns)

        result = {
            "insights": insights,
            "patterns": patterns,
            "statistics": statistics,
            "visualizations": visualizations,
            "data_summary": self._summarize_data(data),
            "agent": self.agent_id
        }

        # Store in history
        self.analysis_history.append({
            "task": description,
            "result": result
        })

        return result

    def _extract_insights(self, data: Any) -> List[str]:
        """
        Extract insights from data.

        Args:
            data: Data to analyze

        Returns:
            List of insights
        """
        insights = []

        if isinstance(data, dict):
            # Analyze dictionary data
            if "results" in data:
                results_data = data["results"]
                if isinstance(results_data, dict):
                    consolidated = results_data.get("consolidated_data", [])
                    if consolidated:
                        insights.append(f"Data consolidated from {len(consolidated)} sources")

                        # Check reliability
                        reliability = results_data.get("reliability_score", 0)
                        if reliability > 0.8:
                            insights.append("High reliability data (>80%)")
                        elif reliability > 0.6:
                            insights.append("Moderate reliability data (60-80%)")
                        else:
                            insights.append("Lower reliability data (<60%)")

            # Check for confidence scores
            if "confidence" in data:
                confidence = data["confidence"]
                insights.append(f"Data confidence level: {confidence * 100:.0f}%")

            # Count data points
            total_items = self._count_data_items(data)
            if total_items > 0:
                insights.append(f"Total data points analyzed: {total_items}")

        elif isinstance(data, list):
            insights.append(f"Analyzed {len(data)} items")
            if data:
                insights.append(f"Data type: {type(data[0]).__name__}")

        else:
            insights.append(f"Data type: {type(data).__name__}")

        # Add generic insights if none found
        if not insights:
            insights.append("Data structure analyzed")
            insights.append("Ready for further processing")

        return insights

    def _detect_patterns(self, data: Any) -> List[Dict[str, Any]]:
        """
        Detect patterns in data.

        Args:
            data: Data to analyze

        Returns:
            List of detected patterns
        """
        patterns = []

        if isinstance(data, dict):
            # Look for repeated structures
            keys = list(data.keys())
            if keys:
                patterns.append({
                    "type": "structure",
                    "description": f"Dictionary with {len(keys)} keys",
                    "details": f"Key patterns: {', '.join(keys[:5])}"
                })

            # Check for nested data
            nested_count = sum(1 for v in data.values() if isinstance(v, (dict, list)))
            if nested_count > 0:
                patterns.append({
                    "type": "nesting",
                    "description": f"Contains {nested_count} nested structures",
                    "details": "Hierarchical data organization"
                })

        elif isinstance(data, list):
            if data:
                # Check data types
                type_counts = Counter(type(item).__name__ for item in data)
                patterns.append({
                    "type": "data_types",
                    "description": "Data type distribution",
                    "details": dict(type_counts)
                })

                # Check for sequences
                if all(isinstance(item, (int, float)) for item in data):
                    patterns.append({
                        "type": "numeric_sequence",
                        "description": "Numeric data sequence",
                        "details": f"Range: {min(data)} to {max(data)}"
                    })

        return patterns

    def _generate_statistics(self, data: Any) -> Dict[str, Any]:
        """
        Generate statistical summary.

        Args:
            data: Data to analyze

        Returns:
            Statistical summary
        """
        stats = {
            "data_type": type(data).__name__,
            "total_size": self._calculate_size(data)
        }

        if isinstance(data, dict):
            stats["key_count"] = len(data)
            stats["has_nested_data"] = any(isinstance(v, (dict, list)) for v in data.values())

        elif isinstance(data, list):
            stats["item_count"] = len(data)
            if data and all(isinstance(item, (int, float)) for item in data):
                stats["numeric_stats"] = {
                    "min": min(data),
                    "max": max(data),
                    "avg": sum(data) / len(data)
                }

        return stats

    def _create_visualizations(
        self,
        insights: List[str],
        patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create visualization metadata.

        Args:
            insights: Extracted insights
            patterns: Detected patterns

        Returns:
            List of visualization specifications
        """
        visualizations = []

        # Suggest bar chart for counts
        if any("count" in str(p).lower() for p in patterns):
            visualizations.append({
                "type": "bar_chart",
                "title": "Data Distribution",
                "description": "Visual representation of data counts"
            })

        # Suggest line chart for sequences
        if any(p.get("type") == "numeric_sequence" for p in patterns):
            visualizations.append({
                "type": "line_chart",
                "title": "Trend Analysis",
                "description": "Visual representation of data trends"
            })

        # Suggest pie chart for distributions
        if any(p.get("type") == "data_types" for p in patterns):
            visualizations.append({
                "type": "pie_chart",
                "title": "Type Distribution",
                "description": "Distribution of data types"
            })

        # Default visualization if none suggested
        if not visualizations:
            visualizations.append({
                "type": "summary_chart",
                "title": "Data Overview",
                "description": "High-level summary visualization"
            })

        return visualizations

    def _summarize_data(self, data: Any) -> str:
        """
        Create a text summary of data.

        Args:
            data: Data to summarize

        Returns:
            Summary text
        """
        if isinstance(data, dict):
            return f"Dictionary with {len(data)} keys"
        elif isinstance(data, list):
            return f"List with {len(data)} items"
        elif isinstance(data, str):
            return f"String with {len(data)} characters"
        else:
            return f"Data of type {type(data).__name__}"

    def _count_data_items(self, data: Any, depth: int = 0, max_depth: int = 3) -> int:
        """
        Recursively count data items.

        Args:
            data: Data to count
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            Total count of items
        """
        if depth > max_depth:
            return 0

        count = 0

        if isinstance(data, dict):
            count += len(data)
            for value in data.values():
                count += self._count_data_items(value, depth + 1, max_depth)
        elif isinstance(data, list):
            count += len(data)
            for item in data:
                count += self._count_data_items(item, depth + 1, max_depth)

        return count

    def _calculate_size(self, data: Any) -> str:
        """
        Calculate approximate size of data.

        Args:
            data: Data to measure

        Returns:
            Size description
        """
        import sys

        size_bytes = sys.getsizeof(data)

        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    async def analyze_trends(self, data: List[Any]) -> Dict[str, Any]:
        """
        Analyze trends in sequential data.

        Args:
            data: Sequential data

        Returns:
            Trend analysis results
        """
        task_data = {
            "task_id": "trend_analysis",
            "description": "Analyze trends in data",
            "parameters": {"data": data}
        }

        return await self.process_task(task_data)

    def get_analysis_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get analysis history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            Analysis history
        """
        history = self.analysis_history
        if limit:
            history = history[-limit:]
        return history
