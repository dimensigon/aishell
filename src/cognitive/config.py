"""
Configuration for cognitive AI features
"""

import os
from pathlib import Path
from typing import Dict, Any

# Base configuration
COGNITIVE_CONFIG = {
    # Memory system
    'memory': {
        'enabled': False,
        'directory': '~/.aishell/memory',
        'vector_dim': 384,
        'max_memories': 100000,
        'learning_rate': 0.1,
        'forgetting_factor': 0.95,
        'use_faiss': True,  # Use FAISS if available, fallback to simple search
    },

    # Anomaly detection
    'anomaly_detection': {
        'enabled': False,
        'collection_interval': 10,  # seconds
        'detection_threshold': 2.0,  # standard deviations
        'auto_remediation': False,  # Require approval for fixes
        'max_remediation_risk': 3,  # 1-5 scale
        'alert_channels': ['log'],  # log, email, slack, webhook
    },

    # Autonomous DevOps
    'autonomous_devops': {
        'enabled': False,
        'auto_scaling': False,
        'auto_optimization': False,
        'auto_deployment': False,  # Very dangerous, keep disabled
        'max_cost_impact': 100.0,  # USD
        'require_approval_above_risk': 3,  # 1-5 scale
        'monitoring_interval': 60,  # seconds
    },

    # MCP Discovery
    'mcp_discovery': {
        'enabled': True,  # Safe to enable by default
        'scan_interval': 300,  # seconds
        'auto_connect': False,  # Manual approval required
    },
}


def get_config(feature: str = None) -> Dict[str, Any]:
    """Get configuration for a specific feature or all features"""
    if feature:
        return COGNITIVE_CONFIG.get(feature, {})
    return COGNITIVE_CONFIG


def update_config(feature: str, updates: Dict[str, Any]) -> bool:
    """Update configuration for a feature"""
    if feature not in COGNITIVE_CONFIG:
        return False

    COGNITIVE_CONFIG[feature].update(updates)
    return True


def load_config_from_env():
    """Load configuration overrides from environment variables"""

    # Memory configuration
    if os.getenv('AISHELL_MEMORY_ENABLED'):
        COGNITIVE_CONFIG['memory']['enabled'] = os.getenv('AISHELL_MEMORY_ENABLED').lower() == 'true'

    if os.getenv('AISHELL_MEMORY_DIR'):
        COGNITIVE_CONFIG['memory']['directory'] = os.getenv('AISHELL_MEMORY_DIR')

    # Anomaly detection configuration
    if os.getenv('AISHELL_ANOMALY_ENABLED'):
        COGNITIVE_CONFIG['anomaly_detection']['enabled'] = os.getenv('AISHELL_ANOMALY_ENABLED').lower() == 'true'

    if os.getenv('AISHELL_AUTO_REMEDIATION'):
        COGNITIVE_CONFIG['anomaly_detection']['auto_remediation'] = os.getenv('AISHELL_AUTO_REMEDIATION').lower() == 'true'

    # Autonomous DevOps configuration
    if os.getenv('AISHELL_DEVOPS_ENABLED'):
        COGNITIVE_CONFIG['autonomous_devops']['enabled'] = os.getenv('AISHELL_DEVOPS_ENABLED').lower() == 'true'

    if os.getenv('AISHELL_AUTO_SCALING'):
        COGNITIVE_CONFIG['autonomous_devops']['auto_scaling'] = os.getenv('AISHELL_AUTO_SCALING').lower() == 'true'


# Load environment overrides on import
load_config_from_env()
