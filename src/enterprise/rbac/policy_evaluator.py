"""Attribute-Based Access Control (ABAC) Policy Evaluator"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json


class PolicyEffect(Enum):
    """Policy effect"""
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class Policy:
    """ABAC Policy"""
    id: str
    name: str
    effect: PolicyEffect
    resources: List[str]
    actions: List[str]
    conditions: Dict[str, Any]
    priority: int = 0


class PolicyEvaluator:
    """Evaluates ABAC policies with conditions"""

    def evaluate(
        self,
        policies: List[Policy],
        resource: str,
        action: str,
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate policies against context"""
        # Sort by priority
        sorted_policies = sorted(policies, key=lambda p: p.priority, reverse=True)

        for policy in sorted_policies:
            if self._matches_resource(policy.resources, resource):
                if action in policy.actions or '*' in policy.actions:
                    if self._evaluate_conditions(policy.conditions, context):
                        return policy.effect == PolicyEffect.ALLOW

        return False

    def _matches_resource(self, resources: List[str], resource: str) -> bool:
        """Check if resource matches policy resources"""
        return resource in resources or '*' in resources

    def _evaluate_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate policy conditions"""
        for key, value in conditions.items():
            if key not in context or context[key] != value:
                return False
        return True
