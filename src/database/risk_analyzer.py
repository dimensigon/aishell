"""SQL risk analyzer with severity level classification."""

from enum import Enum
from typing import Dict, List, Optional
import re


class RiskLevel(Enum):
    """SQL operation risk levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SQLRiskAnalyzer:
    """Analyzes SQL queries for potential risks and assigns severity levels."""

    # Risk patterns with associated risk levels
    RISK_PATTERNS = {
        # CRITICAL - Destructive operations
        r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b': RiskLevel.CRITICAL,
        r'\bTRUNCATE\s+TABLE\b': RiskLevel.CRITICAL,
        r'\bALTER\s+TABLE\s+\w+\s+DROP\b': RiskLevel.CRITICAL,

        # HIGH - Dangerous operations without safety checks
        r'\bUPDATE\s+(?!.*\bWHERE\b)': RiskLevel.HIGH,
        r'\bDELETE\s+FROM\s+(?!.*\bWHERE\b)': RiskLevel.HIGH,
        r'\bGRANT\s+ALL\b': RiskLevel.HIGH,
        r'\bREVOKE\s+ALL\b': RiskLevel.HIGH,

        # MEDIUM - Operations with conditions
        r'\bUPDATE\s+.*\bWHERE\b': RiskLevel.MEDIUM,
        r'\bDELETE\s+FROM\s+.*\bWHERE\b': RiskLevel.MEDIUM,
        r'\bALTER\s+TABLE\b': RiskLevel.MEDIUM,
        r'\bCREATE\s+(TABLE|INDEX|VIEW)\b': RiskLevel.MEDIUM,
        r'\bINSERT\s+INTO\b': RiskLevel.MEDIUM,

        # LOW - Read operations
        r'\bSELECT\s+': RiskLevel.LOW,
        r'\bSHOW\s+': RiskLevel.LOW,
        r'\bDESCRIBE\s+': RiskLevel.LOW,
        r'\bEXPLAIN\s+': RiskLevel.LOW,
    }

    def __init__(self):
        """Initialize the SQL risk analyzer."""
        self.compiled_patterns = {
            re.compile(pattern, re.IGNORECASE): level
            for pattern, level in self.RISK_PATTERNS.items()
        }

    def analyze(self, sql: str) -> Dict[str, any]:
        """Analyze SQL query for risks.

        Args:
            sql: SQL query to analyze

        Returns:
            Dict containing risk level, warnings, and analysis details
        """
        sql = sql.strip()

        # Detect risk level
        risk_level = self._detect_risk_level(sql)

        # Generate warnings
        warnings = self._generate_warnings(sql, risk_level)

        # Check for common issues
        issues = self._check_common_issues(sql)

        # Determine if confirmation is required
        requires_confirmation = risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        return {
            'risk_level': risk_level.value,
            'requires_confirmation': requires_confirmation,
            'warnings': warnings,
            'issues': issues,
            'sql': sql,
            'safe_to_execute': risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM],
        }

    def _detect_risk_level(self, sql: str) -> RiskLevel:
        """Detect the risk level of a SQL query.

        Args:
            sql: SQL query to analyze

        Returns:
            RiskLevel enum value
        """
        # Check patterns from highest to lowest risk
        for pattern, level in sorted(
            self.compiled_patterns.items(),
            key=lambda x: list(RiskLevel).index(x[1]),
            reverse=True
        ):
            if pattern.search(sql):
                return level

        # Default to LOW if no patterns match
        return RiskLevel.LOW

    def _generate_warnings(self, sql: str, risk_level: RiskLevel) -> List[str]:
        """Generate warnings based on risk level.

        Args:
            sql: SQL query
            risk_level: Detected risk level

        Returns:
            List of warning messages
        """
        warnings = []

        if risk_level == RiskLevel.CRITICAL:
            warnings.append("⚠️  CRITICAL: This operation will permanently delete data")
            warnings.append("⚠️  This action cannot be undone")

        elif risk_level == RiskLevel.HIGH:
            if re.search(r'\bUPDATE\s+(?!.*\bWHERE\b)', sql, re.IGNORECASE):
                warnings.append("⚠️  HIGH RISK: UPDATE without WHERE clause will affect ALL rows")
            if re.search(r'\bDELETE\s+FROM\s+(?!.*\bWHERE\b)', sql, re.IGNORECASE):
                warnings.append("⚠️  HIGH RISK: DELETE without WHERE clause will remove ALL rows")
            warnings.append("⚠️  Consider adding a WHERE clause to limit scope")

        elif risk_level == RiskLevel.MEDIUM:
            warnings.append("ℹ️  MEDIUM RISK: This operation will modify data")
            warnings.append("ℹ️  Review the WHERE clause carefully")

        return warnings

    def _check_common_issues(self, sql: str) -> List[str]:
        """Check for common SQL issues.

        Args:
            sql: SQL query

        Returns:
            List of potential issues
        """
        issues = []

        # Check for SQL injection patterns (basic check)
        if re.search(r'[\'\"]\s*OR\s+[\'\"]*\s*1\s*=\s*1', sql, re.IGNORECASE):
            issues.append("Potential SQL injection pattern detected")

        # Check for missing semicolon at end
        if not sql.rstrip().endswith(';'):
            issues.append("Query does not end with semicolon (may cause issues in some contexts)")

        # Check for multiple statements (potential security risk)
        if sql.count(';') > 1:
            issues.append("Multiple statements detected - ensure this is intentional")

        # Check for SELECT *
        if re.search(r'\bSELECT\s+\*', sql, re.IGNORECASE):
            issues.append("SELECT * may impact performance - consider specifying columns")

        return issues

    def get_confirmation_message(self, analysis: Dict[str, any]) -> str:
        """Generate confirmation message for risky operations.

        Args:
            analysis: Analysis result from analyze()

        Returns:
            Formatted confirmation message
        """
        risk_level = analysis['risk_level']
        warnings = analysis['warnings']
        sql = analysis['sql']

        message = f"\n{'='*60}\n"
        message += f"RISK LEVEL: {risk_level}\n"
        message += f"{'='*60}\n\n"

        if warnings:
            message += "Warnings:\n"
            for warning in warnings:
                message += f"  {warning}\n"
            message += "\n"

        message += f"SQL Query:\n  {sql}\n\n"
        message += "Do you want to proceed? (yes/no): "

        return message
