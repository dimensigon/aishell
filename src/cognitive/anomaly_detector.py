"""
Anomaly Detection & Self-Healing System
Detect and fix issues before users notice them
"""

import asyncio
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np
import logging
import psutil
import subprocess

from ..core.health_checks import HealthCheckManager, HealthStatus
from ..cognitive.memory import CognitiveMemory
from ..llm.provider_factory import LLMProviderFactory

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    PERFORMANCE = "performance"
    ERROR_RATE = "error_rate"
    RESOURCE = "resource"
    PATTERN = "pattern"
    SECURITY = "security"
    NETWORK = "network"
    PROCESS = "process"
    DISK = "disk"


class Severity(Enum):
    """Anomaly severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    id: str
    type: AnomalyType
    severity: Severity
    description: str
    metric_name: str
    current_value: float
    expected_value: float
    threshold: float
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    suggested_fixes: List[str] = field(default_factory=list)
    auto_fixable: bool = False


@dataclass
class Metric:
    """A system metric being monitored"""
    name: str
    value: float
    timestamp: float
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class RemediationAction:
    """An action to remediate an anomaly"""
    id: str
    anomaly_id: str
    action_type: str
    command: str
    risk_level: int  # 1-5
    estimated_duration: float
    requires_approval: bool
    rollback_command: Optional[str] = None


class MetricCollector:
    """Collects system metrics for analysis"""

    def __init__(self):
        self.metric_history: Dict[str, List[Metric]] = {}
        self.collection_interval = 10  # seconds

    async def collect(self) -> Dict[str, Metric]:
        """Collect current system metrics"""
        metrics = {}

        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['cpu_usage'] = Metric(
                name='cpu_usage',
                value=cpu_percent,
                timestamp=time.time(),
                unit='percent'
            )

            # Memory metrics
            memory = psutil.virtual_memory()
            metrics['memory_usage'] = Metric(
                name='memory_usage',
                value=memory.percent,
                timestamp=time.time(),
                unit='percent'
            )

            metrics['memory_available'] = Metric(
                name='memory_available',
                value=memory.available / (1024**3),  # Convert to GB
                timestamp=time.time(),
                unit='GB'
            )

            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics['disk_usage'] = Metric(
                name='disk_usage',
                value=disk.percent,
                timestamp=time.time(),
                unit='percent'
            )

            # Network metrics
            net_io = psutil.net_io_counters()
            metrics['network_bytes_sent'] = Metric(
                name='network_bytes_sent',
                value=net_io.bytes_sent,
                timestamp=time.time(),
                unit='bytes'
            )

            metrics['network_bytes_recv'] = Metric(
                name='network_bytes_recv',
                value=net_io.bytes_recv,
                timestamp=time.time(),
                unit='bytes'
            )

            # Process metrics
            process_count = len(psutil.pids())
            metrics['process_count'] = Metric(
                name='process_count',
                value=process_count,
                timestamp=time.time(),
                unit='count'
            )

            # Custom application metrics
            metrics.update(await self._collect_app_metrics())

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

        # Store in history
        for name, metric in metrics.items():
            if name not in self.metric_history:
                self.metric_history[name] = []
            self.metric_history[name].append(metric)

            # Keep only last hour of metrics
            cutoff = time.time() - 3600
            self.metric_history[name] = [
                m for m in self.metric_history[name]
                if m.timestamp > cutoff
            ]

        return metrics

    async def _collect_app_metrics(self) -> Dict[str, Metric]:
        """Collect application-specific metrics"""
        app_metrics = {}

        try:
            # Command execution rate
            # This would integrate with the command processor
            app_metrics['command_rate'] = Metric(
                name='command_rate',
                value=0,  # Would be calculated from command history
                timestamp=time.time(),
                unit='commands/min'
            )

            # Error rate
            app_metrics['error_rate'] = Metric(
                name='error_rate',
                value=0,  # Would be calculated from error logs
                timestamp=time.time(),
                unit='errors/min'
            )

        except Exception as e:
            logger.debug(f"Could not collect app metrics: {e}")

        return app_metrics

    def get_statistics(self, metric_name: str, window: int = 300) -> Dict[str, float]:
        """Get statistics for a metric over a time window"""

        if metric_name not in self.metric_history:
            return {}

        cutoff = time.time() - window
        recent_values = [
            m.value for m in self.metric_history[metric_name]
            if m.timestamp > cutoff
        ]

        if not recent_values:
            return {}

        return {
            'mean': statistics.mean(recent_values),
            'median': statistics.median(recent_values),
            'stdev': statistics.stdev(recent_values) if len(recent_values) > 1 else 0,
            'min': min(recent_values),
            'max': max(recent_values),
            'count': len(recent_values)
        }


class AnomalyDetector:
    """
    Advanced anomaly detection system

    Features:
    - Pattern-based anomaly detection
    - Automatic remediation
    - Predictive maintenance
    - Performance regression detection
    """

    def __init__(self,
                 cognitive_memory: Optional[CognitiveMemory] = None,
                 health_manager: Optional[HealthCheckManager] = None):

        self.cognitive_memory = cognitive_memory
        self.health_manager = health_manager or HealthCheckManager()
        self.metric_collector = MetricCollector()

        # Detection configuration
        self.thresholds = {
            'cpu_usage': {'high': 80, 'critical': 95},
            'memory_usage': {'high': 80, 'critical': 90},
            'disk_usage': {'high': 80, 'critical': 95},
            'error_rate': {'high': 10, 'critical': 50},  # errors per minute
            'process_count': {'high': 500, 'critical': 1000},
        }

        # Anomaly tracking
        self.active_anomalies: Dict[str, Anomaly] = {}
        self.anomaly_history: List[Anomaly] = []
        self.remediation_history: List[RemediationAction] = []

        # Statistical models
        self.baseline_stats: Dict[str, Dict[str, float]] = {}
        self.anomaly_models: Dict[str, Any] = {}

        # Self-healing configuration
        self.auto_remediation_enabled = True
        self.max_auto_fixes_per_hour = 10
        self.recent_fixes: List[float] = []

        # Monitoring state
        self._monitoring = False
        self._monitor_task = None

        # LLM for intelligent analysis
        self.llm_provider = None

    async def start_monitoring(self, interval: int = 10):
        """Start continuous anomaly monitoring"""

        if self._monitoring:
            logger.warning("Monitoring already running")
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop(interval))

        logger.info(f"Started anomaly monitoring (interval: {interval}s)")

    async def stop_monitoring(self):
        """Stop anomaly monitoring"""

        self._monitoring = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped anomaly monitoring")

    async def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""

        while self._monitoring:
            try:
                # Collect metrics
                metrics = await self.metric_collector.collect()

                # Detect anomalies
                anomalies = await self.detect_anomalies(metrics)

                # Process detected anomalies
                for anomaly in anomalies:
                    await self.handle_anomaly(anomaly)

                # Predictive analysis
                await self.predictive_analysis()

                # Sleep until next collection
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)

    async def detect_anomalies(self, metrics: Dict[str, Metric]) -> List[Anomaly]:
        """
        Detect anomalies in current metrics
        """

        anomalies = []
        current_time = time.time()

        # 1. Threshold-based detection
        for metric_name, metric in metrics.items():
            if metric_name in self.thresholds:
                thresholds = self.thresholds[metric_name]

                # Check critical threshold
                if 'critical' in thresholds and metric.value > thresholds['critical']:
                    anomaly = Anomaly(
                        id=f"{metric_name}_{int(current_time)}",
                        type=self._get_anomaly_type(metric_name),
                        severity=Severity.CRITICAL,
                        description=f"{metric_name} critically high: {metric.value:.2f}{metric.unit}",
                        metric_name=metric_name,
                        current_value=metric.value,
                        expected_value=thresholds['high'],
                        threshold=thresholds['critical'],
                        timestamp=current_time,
                        auto_fixable=self._is_auto_fixable(metric_name, Severity.CRITICAL)
                    )
                    anomalies.append(anomaly)

                # Check high threshold
                elif 'high' in thresholds and metric.value > thresholds['high']:
                    anomaly = Anomaly(
                        id=f"{metric_name}_{int(current_time)}",
                        type=self._get_anomaly_type(metric_name),
                        severity=Severity.HIGH,
                        description=f"{metric_name} high: {metric.value:.2f}{metric.unit}",
                        metric_name=metric_name,
                        current_value=metric.value,
                        expected_value=thresholds['high'] * 0.8,
                        threshold=thresholds['high'],
                        timestamp=current_time,
                        auto_fixable=self._is_auto_fixable(metric_name, Severity.HIGH)
                    )
                    anomalies.append(anomaly)

        # 2. Statistical anomaly detection
        statistical_anomalies = await self._detect_statistical_anomalies(metrics)
        anomalies.extend(statistical_anomalies)

        # 3. Pattern-based anomaly detection
        if self.cognitive_memory:
            pattern_anomalies = await self._detect_pattern_anomalies(metrics)
            anomalies.extend(pattern_anomalies)

        # 4. Health check anomalies
        health_anomalies = await self._detect_health_anomalies()
        anomalies.extend(health_anomalies)

        # Filter duplicates
        unique_anomalies = []
        seen_ids = set()

        for anomaly in anomalies:
            if anomaly.id not in seen_ids and anomaly.id not in self.active_anomalies:
                unique_anomalies.append(anomaly)
                seen_ids.add(anomaly.id)

        return unique_anomalies

    async def _detect_statistical_anomalies(self, metrics: Dict[str, Metric]) -> List[Anomaly]:
        """Detect anomalies using statistical methods"""

        anomalies = []

        for metric_name, metric in metrics.items():
            stats = self.metric_collector.get_statistics(metric_name, window=3600)

            if not stats or stats['count'] < 10:
                continue

            # Z-score based detection
            if stats['stdev'] > 0:
                z_score = abs((metric.value - stats['mean']) / stats['stdev'])

                if z_score > 3:  # 3 standard deviations
                    anomaly = Anomaly(
                        id=f"stat_{metric_name}_{int(time.time())}",
                        type=AnomalyType.PATTERN,
                        severity=Severity.MEDIUM if z_score < 4 else Severity.HIGH,
                        description=f"Statistical anomaly in {metric_name}: {z_score:.2f} std deviations",
                        metric_name=metric_name,
                        current_value=metric.value,
                        expected_value=stats['mean'],
                        threshold=stats['mean'] + 3 * stats['stdev'],
                        timestamp=time.time(),
                        context={'z_score': z_score, 'stats': stats}
                    )
                    anomalies.append(anomaly)

        return anomalies

    async def _detect_pattern_anomalies(self, metrics: Dict[str, Metric]) -> List[Anomaly]:
        """Detect anomalies based on learned patterns"""

        anomalies = []

        # Get current context
        context = {
            'metrics': {name: m.value for name, m in metrics.items()},
            'timestamp': time.time()
        }

        # Query cognitive memory for similar situations
        similar_memories = await self.cognitive_memory.recall(
            query=json.dumps(context),
            k=10
        )

        # Check if current situation deviates from past patterns
        for memory in similar_memories:
            if memory.success and 'metrics' in memory.context:
                past_metrics = memory.context['metrics']

                # Compare current vs past metrics
                for metric_name, current_value in context['metrics'].items():
                    if metric_name in past_metrics:
                        past_value = past_metrics[metric_name]
                        deviation = abs(current_value - past_value) / (past_value + 0.01)

                        if deviation > 0.5:  # 50% deviation
                            anomaly = Anomaly(
                                id=f"pattern_{metric_name}_{int(time.time())}",
                                type=AnomalyType.PATTERN,
                                severity=Severity.LOW if deviation < 1.0 else Severity.MEDIUM,
                                description=f"Unusual pattern in {metric_name} compared to history",
                                metric_name=metric_name,
                                current_value=current_value,
                                expected_value=past_value,
                                threshold=past_value * 1.5,
                                timestamp=time.time(),
                                context={'memory_id': memory.id, 'deviation': deviation}
                            )
                            anomalies.append(anomaly)

        return anomalies

    async def _detect_health_anomalies(self) -> List[Anomaly]:
        """Detect anomalies from health checks"""

        anomalies = []

        # Run health checks
        health_results = await self.health_manager.run_all_checks()

        for check_name, result in health_results.items():
            if result.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]:
                severity = Severity.CRITICAL if result.status == HealthStatus.UNHEALTHY else Severity.HIGH

                anomaly = Anomaly(
                    id=f"health_{check_name}_{int(time.time())}",
                    type=AnomalyType.PATTERN,
                    severity=severity,
                    description=f"Health check failed: {check_name} - {result.message}",
                    metric_name=f"health_{check_name}",
                    current_value=0,  # Failed
                    expected_value=1,  # Healthy
                    threshold=0.5,
                    timestamp=time.time(),
                    context={'health_result': result.__dict__},
                    auto_fixable=check_name in ['database', 'filesystem']
                )
                anomalies.append(anomaly)

        return anomalies

    async def handle_anomaly(self, anomaly: Anomaly):
        """
        Handle a detected anomaly
        """

        logger.warning(f"Anomaly detected: {anomaly.description}")

        # Store in active anomalies
        self.active_anomalies[anomaly.id] = anomaly

        # Add to history
        self.anomaly_history.append(anomaly)

        # Generate suggested fixes
        anomaly.suggested_fixes = await self._generate_fixes(anomaly)

        # Store in cognitive memory if available
        if self.cognitive_memory:
            await self.cognitive_memory.remember(
                command=f"ANOMALY_DETECTED: {anomaly.type.value}",
                output=anomaly.description,
                error=None if anomaly.severity in [Severity.LOW, Severity.MEDIUM] else "Requires attention",
                context={'anomaly': anomaly.__dict__},
                duration=0
            )

        # Attempt auto-remediation if enabled
        if self.auto_remediation_enabled and anomaly.auto_fixable:
            await self.attempt_auto_remediation(anomaly)

        # Notify user for high severity
        if anomaly.severity in [Severity.HIGH, Severity.CRITICAL]:
            await self._notify_user(anomaly)

    async def attempt_auto_remediation(self, anomaly: Anomaly) -> bool:
        """
        Attempt to automatically fix an anomaly
        """

        # Check rate limiting
        if not self._can_auto_fix():
            logger.info(f"Auto-remediation rate limited for {anomaly.id}")
            return False

        logger.info(f"Attempting auto-remediation for {anomaly.id}")

        try:
            # Generate remediation action
            action = await self._create_remediation_action(anomaly)

            if not action:
                logger.info(f"No remediation action available for {anomaly.id}")
                return False

            # Validate action safety
            if not await self._validate_remediation(action):
                logger.warning(f"Remediation action failed validation for {anomaly.id}")
                return False

            # Execute remediation
            success = await self._execute_remediation(action)

            if success:
                logger.info(f"Successfully remediated {anomaly.id}")
                # Remove from active anomalies
                del self.active_anomalies[anomaly.id]

                # Record fix
                self.recent_fixes.append(time.time())
                self.remediation_history.append(action)

                # Update cognitive memory
                if self.cognitive_memory:
                    await self.cognitive_memory.learn_from_feedback(
                        memory_id=anomaly.context.get('memory_id', ''),
                        positive=True,
                        feedback=f"Auto-fixed: {action.command}"
                    )

                return True
            else:
                logger.error(f"Remediation failed for {anomaly.id}")

                # Attempt rollback
                if action.rollback_command:
                    await self._execute_rollback(action)

                return False

        except Exception as e:
            logger.error(f"Error during auto-remediation: {e}")
            return False

    async def _create_remediation_action(self, anomaly: Anomaly) -> Optional[RemediationAction]:
        """Create a remediation action for an anomaly"""

        action = None

        # Define remediation strategies
        if anomaly.type == AnomalyType.RESOURCE:
            if anomaly.metric_name == 'memory_usage' and anomaly.severity == Severity.HIGH:
                action = RemediationAction(
                    id=f"fix_{anomaly.id}",
                    anomaly_id=anomaly.id,
                    action_type="clear_cache",
                    command="sync && echo 3 > /proc/sys/vm/drop_caches",
                    risk_level=2,
                    estimated_duration=5.0,
                    requires_approval=False
                )

            elif anomaly.metric_name == 'disk_usage' and anomaly.severity == Severity.HIGH:
                action = RemediationAction(
                    id=f"fix_{anomaly.id}",
                    anomaly_id=anomaly.id,
                    action_type="clean_temp",
                    command="find /tmp -type f -atime +7 -delete",
                    risk_level=2,
                    estimated_duration=10.0,
                    requires_approval=False
                )

        elif anomaly.type == AnomalyType.PROCESS:
            if anomaly.metric_name == 'process_count' and anomaly.severity >= Severity.HIGH:
                action = RemediationAction(
                    id=f"fix_{anomaly.id}",
                    anomaly_id=anomaly.id,
                    action_type="kill_zombies",
                    command="ps aux | grep defunct | awk '{print $2}' | xargs -r kill -9",
                    risk_level=3,
                    estimated_duration=2.0,
                    requires_approval=True
                )

        # Use LLM for intelligent fix generation if available
        if not action and self.llm_provider:
            action = await self._generate_llm_fix(anomaly)

        return action

    async def _generate_llm_fix(self, anomaly: Anomaly) -> Optional[RemediationAction]:
        """Use LLM to generate a fix"""

        if not self.llm_provider:
            try:
                self.llm_provider = await LLMProviderFactory.create_provider(
                    provider='ollama',
                    model='llama2:7b'
                )
            except:
                return None

        prompt = f"""
        System anomaly detected:
        Type: {anomaly.type.value}
        Description: {anomaly.description}
        Metric: {anomaly.metric_name}
        Current Value: {anomaly.current_value}
        Expected Value: {anomaly.expected_value}

        Suggest a safe command to fix this issue. Response format:
        COMMAND: <shell command>
        RISK: <1-5>
        ROLLBACK: <rollback command or 'none'>
        """

        try:
            response = await self.llm_provider.complete(prompt=prompt)

            # Parse response
            lines = response.content.split('\n')
            command = None
            risk = 3
            rollback = None

            for line in lines:
                if line.startswith('COMMAND:'):
                    command = line.replace('COMMAND:', '').strip()
                elif line.startswith('RISK:'):
                    try:
                        risk = int(line.replace('RISK:', '').strip())
                    except:
                        risk = 3
                elif line.startswith('ROLLBACK:'):
                    rollback_text = line.replace('ROLLBACK:', '').strip()
                    if rollback_text.lower() != 'none':
                        rollback = rollback_text

            if command:
                return RemediationAction(
                    id=f"llm_fix_{anomaly.id}",
                    anomaly_id=anomaly.id,
                    action_type="llm_suggested",
                    command=command,
                    risk_level=risk,
                    estimated_duration=10.0,
                    requires_approval=risk >= 4,
                    rollback_command=rollback
                )

        except Exception as e:
            logger.error(f"LLM fix generation failed: {e}")

        return None

    async def _generate_fixes(self, anomaly: Anomaly) -> List[str]:
        """Generate suggested fixes for an anomaly"""

        fixes = []

        # Add standard fixes based on anomaly type
        if anomaly.type == AnomalyType.RESOURCE:
            if 'memory' in anomaly.metric_name:
                fixes.extend([
                    "Clear system caches: sync && echo 3 > /proc/sys/vm/drop_caches",
                    "Identify memory-hungry processes: ps aux --sort=-%mem | head",
                    "Restart memory-intensive services"
                ])
            elif 'disk' in anomaly.metric_name:
                fixes.extend([
                    "Clean temporary files: find /tmp -type f -atime +7 -delete",
                    "Check large files: du -ah / | sort -rh | head -20",
                    "Clean package cache: apt-get clean (or equivalent)"
                ])
            elif 'cpu' in anomaly.metric_name:
                fixes.extend([
                    "Identify CPU-intensive processes: top -b -n 1 | head -20",
                    "Check for runaway processes: ps aux --sort=-%cpu | head",
                    "Consider process nice values"
                ])

        # Query cognitive memory for past fixes
        if self.cognitive_memory:
            similar_fixes = await self.cognitive_memory.recall(
                query=f"fix {anomaly.type.value} {anomaly.metric_name}",
                k=3
            )

            for memory in similar_fixes:
                if memory.success and memory.command.startswith("fix"):
                    fixes.append(f"Past successful fix: {memory.command}")

        return fixes[:5]  # Limit to 5 suggestions

    async def _validate_remediation(self, action: RemediationAction) -> bool:
        """Validate a remediation action is safe to execute"""

        # Check risk level
        if action.risk_level > 3 and not action.requires_approval:
            logger.warning(f"High risk action requires approval: {action.command}")
            return False

        # Check for dangerous commands
        dangerous_keywords = ['rm -rf /', 'dd if=', 'format', '> /dev/sda']
        for keyword in dangerous_keywords:
            if keyword in action.command:
                logger.error(f"Dangerous command blocked: {action.command}")
                return False

        # Validate with cognitive memory if available
        if self.cognitive_memory:
            similar_commands = await self.cognitive_memory.recall(action.command, k=5)

            # Check if similar commands have failed before
            failure_count = sum(1 for m in similar_commands if not m.success)
            if failure_count > len(similar_commands) / 2:
                logger.warning(f"Command has high failure rate in history: {action.command}")
                return False

        return True

    async def _execute_remediation(self, action: RemediationAction) -> bool:
        """Execute a remediation action"""

        try:
            # Log execution
            logger.info(f"Executing remediation: {action.command}")

            # Execute command
            process = await asyncio.create_subprocess_shell(
                action.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=action.estimated_duration
                )
            except asyncio.TimeoutError:
                process.kill()
                logger.error(f"Remediation timed out: {action.command}")
                return False

            # Check result
            if process.returncode == 0:
                logger.info(f"Remediation successful: {action.command}")
                return True
            else:
                logger.error(f"Remediation failed: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error executing remediation: {e}")
            return False

    async def _execute_rollback(self, action: RemediationAction) -> bool:
        """Execute rollback for failed remediation"""

        if not action.rollback_command:
            return False

        try:
            logger.info(f"Executing rollback: {action.rollback_command}")

            process = await asyncio.create_subprocess_shell(
                action.rollback_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info("Rollback successful")
                return True
            else:
                logger.error(f"Rollback failed: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error executing rollback: {e}")
            return False

    async def predictive_analysis(self):
        """Perform predictive analysis to prevent future anomalies"""

        # Analyze trends
        for metric_name in self.metric_collector.metric_history:
            stats = self.metric_collector.get_statistics(metric_name, window=3600)

            if not stats or stats['count'] < 20:
                continue

            # Simple linear regression for trend
            metrics = self.metric_collector.metric_history[metric_name][-20:]
            if len(metrics) < 2:
                continue

            times = [m.timestamp for m in metrics]
            values = [m.value for m in metrics]

            # Calculate trend
            n = len(times)
            sum_x = sum(times)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(times, values))
            sum_x2 = sum(x * x for x in times)

            if n * sum_x2 - sum_x * sum_x == 0:
                continue

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

            # Predict future value (5 minutes)
            future_time = time.time() + 300
            predicted_value = slope * future_time + (sum_y - slope * sum_x) / n

            # Check if predicted value will exceed threshold
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name].get('high', float('inf'))

                if predicted_value > threshold:
                    logger.warning(
                        f"Predictive warning: {metric_name} trending towards threshold. "
                        f"Current: {values[-1]:.2f}, Predicted: {predicted_value:.2f}, "
                        f"Threshold: {threshold}"
                    )

                    # Create predictive anomaly
                    anomaly = Anomaly(
                        id=f"predictive_{metric_name}_{int(time.time())}",
                        type=AnomalyType.PATTERN,
                        severity=Severity.LOW,
                        description=f"Predicted threshold breach for {metric_name} in 5 minutes",
                        metric_name=metric_name,
                        current_value=values[-1],
                        expected_value=predicted_value,
                        threshold=threshold,
                        timestamp=time.time(),
                        context={'trend_slope': slope},
                        auto_fixable=True
                    )

                    await self.handle_anomaly(anomaly)

    async def get_status(self) -> Dict[str, Any]:
        """Get current anomaly detection status"""

        # Clean up old fixes for rate limiting
        self.recent_fixes = [
            t for t in self.recent_fixes
            if t > time.time() - 3600
        ]

        return {
            'monitoring': self._monitoring,
            'active_anomalies': len(self.active_anomalies),
            'anomalies_24h': len([
                a for a in self.anomaly_history
                if a.timestamp > time.time() - 86400
            ]),
            'auto_remediation_enabled': self.auto_remediation_enabled,
            'recent_fixes': len(self.recent_fixes),
            'fixes_remaining': self.max_auto_fixes_per_hour - len(self.recent_fixes),
            'metrics_tracked': len(self.metric_collector.metric_history),
            'current_anomalies': [
                {
                    'id': a.id,
                    'type': a.type.value,
                    'severity': a.severity.name,
                    'description': a.description,
                    'auto_fixable': a.auto_fixable
                }
                for a in self.active_anomalies.values()
            ]
        }

    def _get_anomaly_type(self, metric_name: str) -> AnomalyType:
        """Determine anomaly type from metric name"""

        if 'cpu' in metric_name:
            return AnomalyType.PERFORMANCE
        elif 'memory' in metric_name:
            return AnomalyType.RESOURCE
        elif 'disk' in metric_name:
            return AnomalyType.DISK
        elif 'network' in metric_name:
            return AnomalyType.NETWORK
        elif 'process' in metric_name:
            return AnomalyType.PROCESS
        elif 'error' in metric_name:
            return AnomalyType.ERROR_RATE
        else:
            return AnomalyType.PATTERN

    def _is_auto_fixable(self, metric_name: str, severity: Severity) -> bool:
        """Determine if an anomaly can be auto-fixed"""

        # Only auto-fix non-critical issues
        if severity == Severity.CRITICAL:
            return False

        # Auto-fixable metrics
        auto_fixable = [
            'memory_usage',
            'disk_usage',
            'process_count',
            'cache_size'
        ]

        return metric_name in auto_fixable

    def _can_auto_fix(self) -> bool:
        """Check if we can perform another auto-fix (rate limiting)"""

        # Clean up old fixes
        self.recent_fixes = [
            t for t in self.recent_fixes
            if t > time.time() - 3600
        ]

        return len(self.recent_fixes) < self.max_auto_fixes_per_hour

    async def _notify_user(self, anomaly: Anomaly):
        """Notify user of critical anomaly"""

        # This would integrate with notification system
        logger.critical(f"""
        ⚠️  CRITICAL ANOMALY DETECTED ⚠️
        Type: {anomaly.type.value}
        Severity: {anomaly.severity.name}
        Description: {anomaly.description}
        Suggested Fixes:
        {chr(10).join(f"  - {fix}" for fix in anomaly.suggested_fixes[:3])}
        """)