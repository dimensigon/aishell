"""
Analysis Agent - Performs data analysis and insights

Specialized agent for data analysis, statistical operations,
pattern recognition, and insight generation.
"""

import asyncio
import logging
import statistics
from typing import Any, Dict, List, Optional

from src.agents.base import BaseAgent, AgentCapability, TaskContext

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    """
    Agent specialized in data analysis and insights

    Features:
    - Statistical analysis
    - Pattern recognition
    - Trend analysis
    - Data visualization preparation
    - Report generation
    """

    def __init__(self, agent_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(agent_id=agent_id, config=config, **kwargs)
        self.analysis_results: List[Dict[str, Any]] = []
        self.datasets: Dict[str, List[Any]] = {}

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create analysis execution plan

        Args:
            task: Task context with analysis requirements

        Returns:
            List of planned analysis steps
        """
        analysis_type = task.input_data.get("type", "statistical")
        data_source = task.input_data.get("data_source", "")
        metrics = task.input_data.get("metrics", [])

        plan = []

        # Step 1: Load data
        plan.append(
            {
                "tool": "load_data",
                "params": {
                    "source": data_source,
                    "format": task.input_data.get("format", "auto"),
                },
                "rationale": "Load data for analysis",
            }
        )

        # Step 2: Perform analysis based on type
        if analysis_type == "statistical":
            plan.append(
                {
                    "tool": "statistical_analysis",
                    "params": {"metrics": metrics or ["mean", "median", "std"]},
                    "rationale": "Perform statistical analysis",
                }
            )

        elif analysis_type == "pattern":
            plan.append(
                {
                    "tool": "pattern_analysis",
                    "params": {
                        "patterns": task.input_data.get("patterns", []),
                        "threshold": task.input_data.get("threshold", 0.7),
                    },
                    "rationale": "Detect patterns in data",
                }
            )

        elif analysis_type == "trend":
            plan.append(
                {
                    "tool": "trend_analysis",
                    "params": {
                        "period": task.input_data.get("period", "daily"),
                        "forecast": task.input_data.get("forecast", False),
                    },
                    "rationale": "Analyze trends and forecasts",
                }
            )

        # Step 3: Generate insights
        plan.append(
            {
                "tool": "generate_insights",
                "params": {
                    "format": task.input_data.get("output_format", "summary"),
                    "include_visualizations": task.input_data.get(
                        "visualizations", False
                    ),
                },
                "rationale": "Generate actionable insights from analysis",
            }
        )

        return plan

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an analysis step

        Args:
            step: Step definition

        Returns:
            Step execution result
        """
        tool = step["tool"]
        params = step["params"]

        if tool == "load_data":
            return await self._load_data(params)
        elif tool == "statistical_analysis":
            return await self._statistical_analysis(params)
        elif tool == "pattern_analysis":
            return await self._pattern_analysis(params)
        elif tool == "trend_analysis":
            return await self._trend_analysis(params)
        elif tool == "generate_insights":
            return await self._generate_insights(params)
        else:
            raise ValueError(f"Unknown analysis tool: {tool}")

    async def _load_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load data from source"""
        source = params["source"]
        data_format = params.get("format", "auto")

        logger.info(f"Loading data from: {source}")

        # In real implementation, load from actual source
        # For now, generate sample data
        if isinstance(source, list):
            data = source
        elif isinstance(source, str) and source.startswith("["):
            import json

            data = json.loads(source)
        else:
            # Generate sample data
            data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

        dataset_id = f"dataset_{len(self.datasets)}"
        self.datasets[dataset_id] = data

        return {
            "dataset_id": dataset_id,
            "records": len(data),
            "sample": data[:5] if len(data) > 5 else data,
            "format": data_format,
        }

    async def _statistical_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis"""
        metrics = params.get("metrics", ["mean", "median", "std"])

        logger.info("Performing statistical analysis...")

        # Get most recent dataset
        if not self.datasets:
            return {"error": "No data loaded"}

        dataset_id = list(self.datasets.keys())[-1]
        data = self.datasets[dataset_id]

        # Calculate statistics
        results = {"dataset_id": dataset_id, "count": len(data)}

        try:
            numeric_data = [float(x) for x in data if isinstance(x, (int, float))]

            if not numeric_data:
                return {"error": "No numeric data available"}

            if "mean" in metrics:
                results["mean"] = statistics.mean(numeric_data)

            if "median" in metrics:
                results["median"] = statistics.median(numeric_data)

            if "std" in metrics or "stdev" in metrics:
                if len(numeric_data) > 1:
                    results["std"] = statistics.stdev(numeric_data)
                else:
                    results["std"] = 0.0

            if "min" in metrics:
                results["min"] = min(numeric_data)

            if "max" in metrics:
                results["max"] = max(numeric_data)

            if "variance" in metrics:
                if len(numeric_data) > 1:
                    results["variance"] = statistics.variance(numeric_data)
                else:
                    results["variance"] = 0.0

        except Exception as e:
            logger.error(f"Statistical analysis failed: {e}")
            results["error"] = str(e)

        self.analysis_results.append(results)

        return results

    async def _pattern_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect patterns in data"""
        patterns = params.get("patterns", [])
        threshold = params.get("threshold", 0.7)

        logger.info("Analyzing patterns...")

        if not self.datasets:
            return {"error": "No data loaded"}

        dataset_id = list(self.datasets.keys())[-1]
        data = self.datasets[dataset_id]

        detected_patterns = []

        # Simple pattern detection
        # Check for ascending/descending sequences
        if len(data) >= 3:
            numeric_data = [x for x in data if isinstance(x, (int, float))]

            if len(numeric_data) >= 3:
                # Check ascending
                ascending = sum(
                    1
                    for i in range(len(numeric_data) - 1)
                    if numeric_data[i] < numeric_data[i + 1]
                )
                if ascending / (len(numeric_data) - 1) >= threshold:
                    detected_patterns.append(
                        {
                            "type": "ascending",
                            "confidence": ascending / (len(numeric_data) - 1),
                        }
                    )

                # Check descending
                descending = sum(
                    1
                    for i in range(len(numeric_data) - 1)
                    if numeric_data[i] > numeric_data[i + 1]
                )
                if descending / (len(numeric_data) - 1) >= threshold:
                    detected_patterns.append(
                        {
                            "type": "descending",
                            "confidence": descending / (len(numeric_data) - 1),
                        }
                    )

        result = {
            "dataset_id": dataset_id,
            "patterns_detected": len(detected_patterns),
            "patterns": detected_patterns,
            "threshold": threshold,
        }

        self.analysis_results.append(result)

        return result

    async def _trend_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends in data"""
        period = params.get("period", "daily")
        forecast = params.get("forecast", False)

        logger.info(f"Analyzing trends (period={period})...")

        if not self.datasets:
            return {"error": "No data loaded"}

        dataset_id = list(self.datasets.keys())[-1]
        data = self.datasets[dataset_id]

        numeric_data = [x for x in data if isinstance(x, (int, float))]

        if len(numeric_data) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Calculate simple trend
        first_half = numeric_data[: len(numeric_data) // 2]
        second_half = numeric_data[len(numeric_data) // 2 :]

        avg_first = statistics.mean(first_half) if first_half else 0
        avg_second = statistics.mean(second_half) if second_half else 0

        trend = "stable"
        if avg_second > avg_first * 1.1:
            trend = "increasing"
        elif avg_second < avg_first * 0.9:
            trend = "decreasing"

        result = {
            "dataset_id": dataset_id,
            "trend": trend,
            "period": period,
            "first_half_avg": avg_first,
            "second_half_avg": avg_second,
            "change_percent": ((avg_second - avg_first) / avg_first * 100)
            if avg_first
            else 0,
        }

        if forecast:
            # Simple forecast (last value + trend)
            result["forecast_next"] = numeric_data[-1] + (avg_second - avg_first)

        self.analysis_results.append(result)

        return result

    async def _generate_insights(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from analysis"""
        output_format = params.get("format", "summary")
        include_viz = params.get("include_visualizations", False)

        logger.info("Generating insights...")

        if not self.analysis_results:
            return {
                "insights": "No analysis results available",
                "recommendations": [],
            }

        # Aggregate insights from all analyses
        insights = []

        for result in self.analysis_results:
            if "mean" in result:
                insights.append(f"Average value: {result['mean']:.2f}")
            if "trend" in result:
                insights.append(f"Data trend: {result['trend']}")
            if "patterns_detected" in result:
                insights.append(
                    f"{result['patterns_detected']} patterns detected"
                )

        recommendations = [
            "Continue monitoring data patterns",
            "Consider additional data points for better accuracy",
            "Review outliers and anomalies",
        ]

        synthesis = {
            "insights": insights,
            "recommendations": recommendations,
            "analysis_count": len(self.analysis_results),
            "format": output_format,
        }

        if output_format == "detailed":
            synthesis["detailed_results"] = self.analysis_results

        if include_viz:
            synthesis["visualizations"] = [
                {"type": "line_chart", "data": "time_series"},
                {"type": "bar_chart", "data": "statistics"},
            ]

        return synthesis

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate analysis step safety

        Args:
            step: Step to validate

        Returns:
            Safety validation result
        """
        # Analysis operations are generally safe
        return {
            "requires_approval": False,
            "safe": True,
            "risk_level": "low",
            "risks": [],
            "mitigations": [],
        }

    def get_analysis_results(self) -> List[Dict[str, Any]]:
        """Get all analysis results"""
        return self.analysis_results

    def get_dataset(self, dataset_id: str) -> Optional[List[Any]]:
        """Get a specific dataset"""
        return self.datasets.get(dataset_id)

    def clear_results(self) -> None:
        """Clear analysis results and datasets"""
        self.analysis_results.clear()
        self.datasets.clear()
