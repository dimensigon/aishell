"""
Cognitive AI Features for AIShell
Feature-flagged integration for gradual adoption
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Feature flags - start disabled for safety
FEATURES = {
    'cognitive_memory': False,      # FAISS-based semantic memory
    'anomaly_detection': False,     # ML anomaly detection with auto-remediation
    'autonomous_devops': False,     # Self-managing infrastructure
    'mcp_discovery': True           # MCP Auto-Discovery (safe to enable)
}

# Lazy loading for heavy dependencies
_cognitive_memory = None
_anomaly_detector = None
_autonomous_devops = None


def enable_feature(feature_name: str) -> bool:
    """Enable a cognitive feature at runtime"""
    if feature_name in FEATURES:
        FEATURES[feature_name] = True
        logger.info(f"Enabled cognitive feature: {feature_name}")
        return True
    logger.warning(f"Unknown feature: {feature_name}")
    return False


def disable_feature(feature_name: str) -> bool:
    """Disable a cognitive feature at runtime"""
    if feature_name in FEATURES:
        FEATURES[feature_name] = False
        logger.info(f"Disabled cognitive feature: {feature_name}")
        return True
    logger.warning(f"Unknown feature: {feature_name}")
    return False


def is_enabled(feature_name: str) -> bool:
    """Check if a cognitive feature is enabled"""
    return FEATURES.get(feature_name, False)


def get_cognitive_memory():
    """Lazy load cognitive memory system"""
    global _cognitive_memory

    if not is_enabled('cognitive_memory'):
        logger.debug("Cognitive memory feature is disabled")
        return None

    if _cognitive_memory is None:
        try:
            from .memory import CognitiveMemory
            _cognitive_memory = CognitiveMemory()
            logger.info("Initialized cognitive memory system")
        except ImportError as e:
            logger.error(f"Failed to load cognitive memory: {e}")
            logger.info("Install dependencies: pip install faiss-cpu numpy")
            disable_feature('cognitive_memory')
            return None
        except Exception as e:
            logger.error(f"Error initializing cognitive memory: {e}")
            disable_feature('cognitive_memory')
            return None

    return _cognitive_memory


def get_anomaly_detector():
    """Lazy load anomaly detection system"""
    global _anomaly_detector

    if not is_enabled('anomaly_detection'):
        logger.debug("Anomaly detection feature is disabled")
        return None

    if _anomaly_detector is None:
        try:
            from .anomaly_detector import AnomalyDetector
            _anomaly_detector = AnomalyDetector()
            logger.info("Initialized anomaly detection system")
        except ImportError as e:
            logger.error(f"Failed to load anomaly detector: {e}")
            logger.info("Install dependencies: pip install psutil numpy")
            disable_feature('anomaly_detection')
            return None
        except Exception as e:
            logger.error(f"Error initializing anomaly detector: {e}")
            disable_feature('anomaly_detection')
            return None

    return _anomaly_detector


def get_autonomous_devops():
    """Lazy load autonomous DevOps system"""
    global _autonomous_devops

    if not is_enabled('autonomous_devops'):
        logger.debug("Autonomous DevOps feature is disabled")
        return None

    if _autonomous_devops is None:
        try:
            from .autonomous_devops import AutonomousDevOps
            _autonomous_devops = AutonomousDevOps()
            logger.info("Initialized autonomous DevOps system")
        except ImportError as e:
            logger.error(f"Failed to load autonomous DevOps: {e}")
            logger.info("Install cognitive dependencies")
            disable_feature('autonomous_devops')
            return None
        except Exception as e:
            logger.error(f"Error initializing autonomous DevOps: {e}")
            disable_feature('autonomous_devops')
            return None

    return _autonomous_devops


__all__ = [
    'FEATURES',
    'enable_feature',
    'disable_feature',
    'is_enabled',
    'get_cognitive_memory',
    'get_anomaly_detector',
    'get_autonomous_devops',
]
