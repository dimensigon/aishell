"""
Performance monitoring and alerting for enterprise features.

Provides real-time performance tracking, slow query detection, and alerting.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import threading
import json
import psutil


@dataclass
class QueryMetrics:
    """Metrics for a query execution."""
    query: str
    execution_time: float
    rows: int
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """Monitor database and system performance."""

    def __init__(
        self,
        slow_query_threshold: float = 1.0,
        high_memory_threshold: int = 2048,
        error_rate_threshold: float = 0.1,
        webhook_url: Optional[str] = None
    ):
        """Initialize performance monitor."""
        self.config = {
            'slow_query_threshold': slow_query_threshold,
            'high_memory_threshold': high_memory_threshold,
            'error_rate_threshold': error_rate_threshold
        }
        self._webhook_url = webhook_url
        self._queries: List[QueryMetrics] = []
        self._slow_queries: List[QueryMetrics] = []
        self._lock = threading.Lock()
        self._memory_samples: List[Dict[str, float]] = []

    def record_query(self, query: str, execution_time: float, rows: int) -> None:
        """Record a query execution."""
        with self._lock:
            metrics = QueryMetrics(
                query=query,
                execution_time=execution_time,
                rows=rows
            )
            self._queries.append(metrics)

            if execution_time > self.config['slow_query_threshold']:
                self._slow_queries.append(metrics)

    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics."""
        if not self._queries:
            return {
                'total_queries': 0,
                'avg_execution_time': 0.0,
                'max_execution_time': 0.0,
                'min_execution_time': 0.0
            }

        execution_times = [q.execution_time for q in self._queries]

        return {
            'total_queries': len(self._queries),
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'max_execution_time': max(execution_times),
            'min_execution_time': min(execution_times),
            'slow_query_count': len(self._slow_queries)
        }

    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get slow query details."""
        return [
            {
                'query': q.query,
                'execution_time': q.execution_time,
                'rows': q.rows,
                'timestamp': q.timestamp.isoformat()
            }
            for q in self._slow_queries
        ]

    def track_memory_usage(self) -> None:
        """Track current memory usage."""
        memory_info = psutil.virtual_memory()

        sample = {
            'timestamp': datetime.now().isoformat(),
            'current_memory_mb': memory_info.used / (1024 * 1024),
            'percent': memory_info.percent
        }

        with self._lock:
            self._memory_samples.append(sample)

            if len(self._memory_samples) > 100:
                self._memory_samples = self._memory_samples[-100:]

    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory usage metrics."""
        if not self._memory_samples:
            self.track_memory_usage()

        if self._memory_samples:
            current = self._memory_samples[-1]['current_memory_mb']
            peak = max(s['current_memory_mb'] for s in self._memory_samples)

            return {
                'current_memory_mb': current,
                'peak_memory_mb': peak,
                'samples': len(self._memory_samples)
            }

        return {
            'current_memory_mb': 0,
            'peak_memory_mb': 0,
            'samples': 0
        }

    def send_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Send alert via webhook."""
        if not self._webhook_url:
            return

        alert_payload = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        try:
            import requests
            requests.post(self._webhook_url, json=alert_payload, timeout=5)
        except Exception:
            pass

    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics for dashboard."""
        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'queries': {
                'total': len(self._queries),
                'slow': len(self._slow_queries),
                'metrics': self.get_metrics()
            },
            'performance': {
                'slow_queries': self.get_slow_queries()
            },
            'memory': self.get_memory_metrics()
        }

        if format == 'json':
            return json.dumps(metrics_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Backward compatibility alias
SystemMonitor = PerformanceMonitor
