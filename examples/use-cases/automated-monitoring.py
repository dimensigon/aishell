#!/usr/bin/env python3
"""
Automated Database Monitoring Agent for agentic-aishell

This example demonstrates how to build an autonomous monitoring agent that:
- Tracks database performance metrics continuously
- Detects anomalies and performance degradation
- Sends alerts when thresholds are exceeded
- Generates optimization recommendations
- Can self-heal common performance issues

See examples/use-cases/README.md for full documentation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Database performance metric"""
    timestamp: datetime
    metric_name: str
    value: float
    threshold: float
    status: str  # 'normal', 'warning', 'critical'


@dataclass
class Alert:
    """Performance alert"""
    timestamp: datetime
    severity: str  # 'info', 'warning', 'critical'
    metric: str
    message: str
    recommendation: Optional[str] = None


class DatabaseMonitoringAgent:
    """
    Autonomous database monitoring agent with self-healing capabilities.

    Features:
    - Real-time performance monitoring
    - Anomaly detection using statistical methods
    - Automatic alerting with configurable thresholds
    - Self-healing for common performance issues
    - Historical trend analysis
    """

    def __init__(
        self,
        check_interval: int = 60,
        alert_threshold: Dict[str, float] = None
    ):
        """
        Initialize monitoring agent.

        Args:
            check_interval: Seconds between health checks (default: 60)
            alert_threshold: Custom thresholds for alerts
        """
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold or {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'query_time': 1000.0,  # milliseconds
            'connection_count': 80.0,  # percentage of max
            'lock_count': 100,
            'deadlock_count': 1
        }
        self.metrics_history: List[PerformanceMetric] = []
        self.alerts: List[Alert] = []
        self.running = False

    async def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        logger.info("Starting database monitoring agent...")

        try:
            while self.running:
                await self._monitor_cycle()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            self.running = False

    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("Stopping database monitoring agent...")

    async def _monitor_cycle(self):
        """Single monitoring cycle"""
        logger.info("Running monitoring cycle...")

        # Collect metrics
        metrics = await self._collect_metrics()

        # Analyze metrics
        anomalies = self._detect_anomalies(metrics)

        # Generate alerts
        if anomalies:
            await self._generate_alerts(anomalies)

        # Attempt self-healing if enabled
        if anomalies:
            await self._attempt_self_healing(anomalies)

        # Store metrics history
        self.metrics_history.extend(metrics)

        # Cleanup old metrics (keep last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]

    async def _collect_metrics(self) -> List[PerformanceMetric]:
        """
        Collect database performance metrics.

        In a real implementation, this would query the database using
        agentic-aishell's MCP clients.
        """
        now = datetime.now()
        metrics = []

        # Simulate metric collection
        # Replace with actual database queries
        sample_metrics = {
            'cpu_usage': 65.0,
            'memory_usage': 72.0,
            'disk_usage': 45.0,
            'query_time': 250.0,
            'connection_count': 45.0,
            'lock_count': 12,
            'deadlock_count': 0
        }

        for name, value in sample_metrics.items():
            threshold = self.alert_threshold.get(name, 0)
            status = self._calculate_status(value, threshold)

            metric = PerformanceMetric(
                timestamp=now,
                metric_name=name,
                value=value,
                threshold=threshold,
                status=status
            )
            metrics.append(metric)

        return metrics

    def _calculate_status(self, value: float, threshold: float) -> str:
        """Calculate metric status based on threshold"""
        if value >= threshold:
            return 'critical'
        elif value >= threshold * 0.8:
            return 'warning'
        return 'normal'

    def _detect_anomalies(
        self,
        metrics: List[PerformanceMetric]
    ) -> List[PerformanceMetric]:
        """
        Detect anomalies in metrics using statistical analysis.

        In production, you would use more sophisticated methods:
        - Moving averages
        - Standard deviation analysis
        - Machine learning models
        """
        anomalies = [
            m for m in metrics
            if m.status in ('warning', 'critical')
        ]
        return anomalies

    async def _generate_alerts(self, anomalies: List[PerformanceMetric]):
        """Generate alerts for detected anomalies"""
        for metric in anomalies:
            severity = 'critical' if metric.status == 'critical' else 'warning'

            alert = Alert(
                timestamp=metric.timestamp,
                severity=severity,
                metric=metric.metric_name,
                message=f"{metric.metric_name} is {metric.value:.2f} "
                        f"(threshold: {metric.threshold:.2f})",
                recommendation=self._get_recommendation(metric)
            )

            self.alerts.append(alert)
            logger.warning(f"Alert: {alert.message}")

            # In production, send to monitoring system
            # await self._send_to_monitoring_system(alert)

    def _get_recommendation(self, metric: PerformanceMetric) -> str:
        """Get optimization recommendation for metric"""
        recommendations = {
            'cpu_usage': "Consider optimizing slow queries or adding indexes",
            'memory_usage': "Review connection pooling and query result caching",
            'disk_usage': "Archive old data or increase storage capacity",
            'query_time': "Add indexes or rewrite inefficient queries",
            'connection_count': "Increase max connections or optimize connection usage",
            'lock_count': "Review transaction isolation levels and query patterns",
            'deadlock_count': "Analyze deadlock logs and optimize transaction order"
        }
        return recommendations.get(metric.metric_name, "Manual investigation required")

    async def _attempt_self_healing(self, anomalies: List[PerformanceMetric]):
        """
        Attempt to automatically fix common issues.

        In production, implement with caution and proper safeguards.
        """
        for metric in anomalies:
            if metric.metric_name == 'lock_count' and metric.value > 50:
                logger.info("Attempting to identify and kill long-running transactions...")
                # await self._kill_long_transactions()

            elif metric.metric_name == 'connection_count' and metric.value > 90:
                logger.info("Attempting to recycle idle connections...")
                # await self._recycle_idle_connections()

    def get_health_summary(self) -> Dict:
        """Get current health summary"""
        if not self.metrics_history:
            return {'status': 'unknown', 'message': 'No metrics collected yet'}

        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > datetime.now() - timedelta(minutes=5)
        ]

        critical_count = sum(1 for m in recent_metrics if m.status == 'critical')
        warning_count = sum(1 for m in recent_metrics if m.status == 'warning')

        if critical_count > 0:
            status = 'critical'
        elif warning_count > 0:
            status = 'warning'
        else:
            status = 'healthy'

        return {
            'status': status,
            'critical_alerts': critical_count,
            'warnings': warning_count,
            'total_metrics': len(recent_metrics),
            'last_check': recent_metrics[-1].timestamp if recent_metrics else None
        }


async def main():
    """Example usage"""
    print("=== Automated Database Monitoring Agent ===\n")
    print("This agent continuously monitors database performance and")
    print("automatically detects and responds to issues.\n")

    # Create monitoring agent
    agent = DatabaseMonitoringAgent(
        check_interval=30,  # Check every 30 seconds
        alert_threshold={
            'cpu_usage': 75.0,
            'memory_usage': 80.0,
            'query_time': 500.0
        }
    )

    # Start monitoring (runs for 3 cycles as demo)
    monitor_task = asyncio.create_task(agent.start_monitoring())

    # Run for 2 minutes then stop
    await asyncio.sleep(120)
    await agent.stop_monitoring()

    # Show summary
    print("\n=== Monitoring Summary ===")
    summary = agent.get_health_summary()
    print(f"Status: {summary['status']}")
    print(f"Critical Alerts: {summary['critical_alerts']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Total Metrics Collected: {len(agent.metrics_history)}")
    print(f"\nTotal Alerts Generated: {len(agent.alerts)}")

    if agent.alerts:
        print("\nRecent Alerts:")
        for alert in agent.alerts[-5:]:
            print(f"  [{alert.severity.upper()}] {alert.message}")
            if alert.recommendation:
                print(f"    ’ {alert.recommendation}")


if __name__ == "__main__":
    print("Automated Monitoring Agent for agentic-aishell")
    print("See examples/use-cases/README.md for full documentation\n")
    asyncio.run(main())
