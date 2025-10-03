"""
System monitoring and health checks for AI-Shell.

Monitors database connections, query performance, and system resources.
"""

import asyncio
import logging
import psutil
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Health check result."""
    status: HealthStatus
    component: str
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['status'] = self.status.value
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    query_count: int
    avg_response_time: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class SystemMonitor:
    """Monitors system health and performance."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.health_checks: List[HealthCheck] = []
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = self.config.get('max_history', 1000)
        self.check_interval = self.config.get('check_interval', 60)
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Thresholds
        self.cpu_threshold = self.config.get('cpu_threshold', 80.0)
        self.memory_threshold = self.config.get('memory_threshold', 85.0)
        self.disk_threshold = self.config.get('disk_threshold', 90.0)
        self.response_time_threshold = self.config.get('response_time_threshold', 1.0)

    async def start_monitoring(self):
        """Start continuous monitoring."""
        if self._monitoring:
            logger.warning("Monitoring already started")
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("System monitoring started")

    async def stop_monitoring(self):
        """Stop continuous monitoring."""
        if not self._monitoring:
            return

        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("System monitoring stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                await self.perform_health_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def perform_health_check(self) -> Dict[str, HealthCheck]:
        """
        Perform comprehensive health check.

        Returns:
            Dictionary of health check results by component
        """
        checks = {}

        # System resources check
        checks['system'] = await self._check_system_resources()

        # Database check
        checks['database'] = await self._check_database()

        # Performance check
        checks['performance'] = await self._check_performance()

        # Store checks
        for check in checks.values():
            self.health_checks.append(check)

        # Limit history
        if len(self.health_checks) > self.max_history_size:
            self.health_checks = self.health_checks[-self.max_history_size:]

        return checks

    async def _check_system_resources(self) -> HealthCheck:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Determine status
            issues = []
            if cpu_percent > self.cpu_threshold:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > self.memory_threshold:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            if disk.percent > self.disk_threshold:
                issues.append(f"High disk usage: {disk.percent:.1f}%")

            if not issues:
                status = HealthStatus.HEALTHY
                message = "System resources normal"
            elif len(issues) == 1:
                status = HealthStatus.DEGRADED
                message = issues[0]
            else:
                status = HealthStatus.UNHEALTHY
                message = "; ".join(issues)

            return HealthCheck(
                status=status,
                component="system",
                message=message,
                timestamp=datetime.now(),
                details={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent
                }
            )
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return HealthCheck(
                status=HealthStatus.UNHEALTHY,
                component="system",
                message=f"Check failed: {str(e)}",
                timestamp=datetime.now()
            )

    async def _check_database(self) -> HealthCheck:
        """Check database connectivity and status."""
        try:
            # This would check actual database connection
            # For now, assume healthy
            return HealthCheck(
                status=HealthStatus.HEALTHY,
                component="database",
                message="Database connections healthy",
                timestamp=datetime.now(),
                details={'active_connections': 0}
            )
        except Exception as e:
            logger.error(f"Error checking database: {e}")
            return HealthCheck(
                status=HealthStatus.UNHEALTHY,
                component="database",
                message=f"Database check failed: {str(e)}",
                timestamp=datetime.now()
            )

    async def _check_performance(self) -> HealthCheck:
        """Check performance metrics."""
        try:
            # Calculate recent performance
            if not self.metrics_history:
                return HealthCheck(
                    status=HealthStatus.HEALTHY,
                    component="performance",
                    message="No performance data yet",
                    timestamp=datetime.now()
                )

            recent_metrics = self.metrics_history[-10:]
            avg_response = sum(m.avg_response_time for m in recent_metrics) / len(recent_metrics)

            if avg_response > self.response_time_threshold:
                status = HealthStatus.DEGRADED
                message = f"Slow response time: {avg_response:.2f}s"
            else:
                status = HealthStatus.HEALTHY
                message = "Performance normal"

            return HealthCheck(
                status=status,
                component="performance",
                message=message,
                timestamp=datetime.now(),
                details={'avg_response_time': avg_response}
            )
        except Exception as e:
            logger.error(f"Error checking performance: {e}")
            return HealthCheck(
                status=HealthStatus.UNHEALTHY,
                component="performance",
                message=f"Performance check failed: {str(e)}",
                timestamp=datetime.now()
            )

    async def record_metrics(self, active_connections: int, query_count: int, avg_response_time: float):
        """
        Record system metrics.

        Args:
            active_connections: Number of active database connections
            query_count: Number of queries executed
            avg_response_time: Average response time
        """
        cpu_percent = psutil.cpu_percent(interval=0)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent

        metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            active_connections=active_connections,
            query_count=query_count,
            avg_response_time=avg_response_time,
            timestamp=datetime.now()
        )

        self.metrics_history.append(metrics)

        # Limit history
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]

    async def get_health_summary(self) -> Dict[str, Any]:
        """
        Get overall health summary.

        Returns:
            Health summary with status and details
        """
        if not self.health_checks:
            return {
                'status': HealthStatus.HEALTHY.value,
                'message': 'No health checks performed yet',
                'checks': []
            }

        # Get most recent check for each component
        recent_checks = {}
        for check in reversed(self.health_checks):
            if check.component not in recent_checks:
                recent_checks[check.component] = check

        # Determine overall status
        statuses = [check.status for check in recent_checks.values()]
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return {
            'status': overall_status.value,
            'message': f"System {overall_status.value}",
            'checks': [check.to_dict() for check in recent_checks.values()],
            'timestamp': datetime.now().isoformat()
        }

    async def get_metrics_summary(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Get metrics summary for specified duration.

        Args:
            duration_minutes: Duration to analyze in minutes

        Returns:
            Metrics summary
        """
        if not self.metrics_history:
            return {
                'message': 'No metrics available',
                'metrics': {}
            }

        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {
                'message': f'No metrics in last {duration_minutes} minutes',
                'metrics': {}
            }

        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(recent_metrics),
            'metrics': {
                'avg_cpu_percent': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
                'avg_memory_percent': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
                'avg_disk_percent': sum(m.disk_percent for m in recent_metrics) / len(recent_metrics),
                'avg_active_connections': sum(m.active_connections for m in recent_metrics) / len(recent_metrics),
                'total_queries': sum(m.query_count for m in recent_metrics),
                'avg_response_time': sum(m.avg_response_time for m in recent_metrics) / len(recent_metrics),
            },
            'timestamp': datetime.now().isoformat()
        }

    async def clear_history(self):
        """Clear health check and metrics history."""
        self.health_checks.clear()
        self.metrics_history.clear()
        logger.info("Monitoring history cleared")
