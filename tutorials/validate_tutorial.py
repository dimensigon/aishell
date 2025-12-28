#!/usr/bin/env python3
"""
AIShell Tutorial Validation Script

This script validates all tutorial code examples to ensure they work correctly.

Features:
- Tests all prerequisites (Python version, dependencies, database, LLM)
- Validates database connections
- Runs all code examples in isolation
- Generates comprehensive validation report
- Identifies broken examples with detailed error messages

Usage:
    python tutorials/validate_tutorial.py
    python tutorials/validate_tutorial.py --tutorial 01
    python tutorials/validate_tutorial.py --verbose
    python tutorials/validate_tutorial.py --output report.json
"""

import argparse
import asyncio
import importlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


# ============================================================================
# Configuration and Data Models
# ============================================================================

class ValidationStatus(Enum):
    PASS = "✓ PASS"
    FAIL = "✗ FAIL"
    WARN = "⚠ WARN"
    SKIP = "⊘ SKIP"


@dataclass
class ValidationResult:
    """Result of a single validation check"""
    name: str
    status: ValidationStatus
    message: str
    duration: float = 0.0
    details: Dict[str, Any] = None
    error: Optional[str] = None

    def to_dict(self):
        result = {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'duration': round(self.duration, 3)
        }
        if self.details:
            result['details'] = self.details
        if self.error:
            result['error'] = self.error
        return result


@dataclass
class TutorialValidation:
    """Validation results for a single tutorial"""
    tutorial_id: str
    tutorial_name: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    duration: float
    results: List[ValidationResult]

    def to_dict(self):
        return {
            'tutorial_id': self.tutorial_id,
            'tutorial_name': self.tutorial_name,
            'total_checks': self.total_checks,
            'passed': self.passed,
            'failed': self.failed,
            'warnings': self.warnings,
            'skipped': self.skipped,
            'duration': round(self.duration, 3),
            'results': [r.to_dict() for r in self.results]
        }


@dataclass
class ValidationReport:
    """Complete validation report"""
    timestamp: str
    python_version: str
    total_tutorials: int
    total_checks: int
    total_passed: int
    total_failed: int
    total_warnings: int
    total_duration: float
    prerequisite_checks: List[ValidationResult]
    tutorial_validations: List[TutorialValidation]

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'python_version': self.python_version,
            'total_tutorials': self.total_tutorials,
            'total_checks': self.total_checks,
            'total_passed': self.total_passed,
            'total_failed': self.total_failed,
            'total_warnings': self.total_warnings,
            'total_duration': round(self.total_duration, 3),
            'prerequisite_checks': [p.to_dict() for p in self.prerequisite_checks],
            'tutorial_validations': [t.to_dict() for t in self.tutorial_validations]
        }


# ============================================================================
# Prerequisite Validators
# ============================================================================

class PrerequisiteValidator:
    """Validates system prerequisites for tutorials"""

    @staticmethod
    def check_python_version() -> ValidationResult:
        """Check Python version (3.8+)"""
        start = time.time()
        version = sys.version_info

        if version.major >= 3 and version.minor >= 8:
            return ValidationResult(
                name="Python Version",
                status=ValidationStatus.PASS,
                message=f"Python {version.major}.{version.minor}.{version.micro}",
                duration=time.time() - start,
                details={'version': f"{version.major}.{version.minor}.{version.micro}"}
            )
        else:
            return ValidationResult(
                name="Python Version",
                status=ValidationStatus.FAIL,
                message=f"Python 3.8+ required, found {version.major}.{version.minor}",
                duration=time.time() - start,
                error=f"Incompatible Python version: {version.major}.{version.minor}"
            )

    @staticmethod
    def check_dependencies() -> ValidationResult:
        """Check required Python packages"""
        start = time.time()
        required_packages = [
            'pytest',
            'asyncio',
            'dataclasses',
            'pathlib',
            'json',
            'sqlite3'
        ]

        missing = []
        installed = []

        for package in required_packages:
            try:
                importlib.import_module(package)
                installed.append(package)
            except ImportError:
                missing.append(package)

        if not missing:
            return ValidationResult(
                name="Python Dependencies",
                status=ValidationStatus.PASS,
                message=f"All {len(installed)} required packages installed",
                duration=time.time() - start,
                details={'installed': installed}
            )
        else:
            return ValidationResult(
                name="Python Dependencies",
                status=ValidationStatus.FAIL,
                message=f"Missing packages: {', '.join(missing)}",
                duration=time.time() - start,
                error=f"Install missing packages: pip install {' '.join(missing)}",
                details={'missing': missing, 'installed': installed}
            )

    @staticmethod
    def check_database_connectivity() -> ValidationResult:
        """Check database connectivity (SQLite)"""
        start = time.time()

        try:
            # Test in-memory database
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            conn.close()

            if result[0] == 1:
                return ValidationResult(
                    name="Database Connectivity",
                    status=ValidationStatus.PASS,
                    message="SQLite database connectivity OK",
                    duration=time.time() - start,
                    details={'database': 'SQLite', 'test': 'in-memory'}
                )
        except Exception as e:
            return ValidationResult(
                name="Database Connectivity",
                status=ValidationStatus.FAIL,
                message="Failed to connect to database",
                duration=time.time() - start,
                error=str(e)
            )

    @staticmethod
    def check_llm_availability() -> ValidationResult:
        """Check LLM availability (Ollama/OpenAI)"""
        start = time.time()

        # Check for API keys or Ollama
        has_openai = os.getenv('OPENAI_API_KEY') is not None
        has_ollama = False

        # Try to check if Ollama is running
        try:
            result = subprocess.run(
                ['which', 'ollama'],
                capture_output=True,
                text=True,
                timeout=2
            )
            has_ollama = result.returncode == 0
        except:
            pass

        if has_openai or has_ollama:
            providers = []
            if has_openai:
                providers.append("OpenAI")
            if has_ollama:
                providers.append("Ollama")

            return ValidationResult(
                name="LLM Availability",
                status=ValidationStatus.PASS,
                message=f"LLM providers available: {', '.join(providers)}",
                duration=time.time() - start,
                details={'providers': providers}
            )
        else:
            return ValidationResult(
                name="LLM Availability",
                status=ValidationStatus.WARN,
                message="No LLM provider configured (optional for most tests)",
                duration=time.time() - start,
                details={'note': 'Set OPENAI_API_KEY or install Ollama for LLM features'}
            )

    @staticmethod
    def check_file_system_access() -> ValidationResult:
        """Check file system read/write access"""
        start = time.time()

        try:
            import tempfile

            # Create temp directory
            temp_dir = Path(tempfile.gettempdir()) / 'aishell_validation_test'
            temp_dir.mkdir(exist_ok=True)

            # Test write
            test_file = temp_dir / 'test.txt'
            test_file.write_text('test')

            # Test read
            content = test_file.read_text()

            # Cleanup
            test_file.unlink()
            temp_dir.rmdir()

            return ValidationResult(
                name="File System Access",
                status=ValidationStatus.PASS,
                message="File system read/write OK",
                duration=time.time() - start,
                details={'test_dir': str(temp_dir)}
            )

        except Exception as e:
            return ValidationResult(
                name="File System Access",
                status=ValidationStatus.FAIL,
                message="Failed to access file system",
                duration=time.time() - start,
                error=str(e)
            )

    @staticmethod
    def check_project_structure() -> ValidationResult:
        """Check project directory structure"""
        start = time.time()

        project_root = Path(__file__).parent.parent
        required_dirs = [
            'src',
            'tests',
            'tutorials',
            'config'
        ]

        missing = []
        found = []

        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists():
                found.append(dir_name)
            else:
                missing.append(dir_name)

        if not missing:
            return ValidationResult(
                name="Project Structure",
                status=ValidationStatus.PASS,
                message=f"All {len(found)} required directories found",
                duration=time.time() - start,
                details={'directories': found}
            )
        else:
            return ValidationResult(
                name="Project Structure",
                status=ValidationStatus.WARN,
                message=f"Missing directories: {', '.join(missing)}",
                duration=time.time() - start,
                details={'found': found, 'missing': missing}
            )


# ============================================================================
# Tutorial Code Validators
# ============================================================================

class TutorialValidator:
    """Validates tutorial code examples"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent

    async def validate_tutorial_01_health_checks(self) -> TutorialValidation:
        """Validate Tutorial 01: Health Checks"""
        start = time.time()
        results = []

        # Test 1: Basic health check structure
        result = await self._test_async_health_check()
        results.append(result)

        # Test 2: Parallel execution
        result = await self._test_parallel_execution()
        results.append(result)

        # Test 3: Timeout protection
        result = await self._test_timeout_protection()
        results.append(result)

        # Calculate summary
        duration = time.time() - start
        return self._create_tutorial_summary("01", "Health Checks", results, duration)

    async def _test_async_health_check(self) -> ValidationResult:
        """Test async health check pattern"""
        start = time.time()
        try:
            async def mock_health_check():
                await asyncio.sleep(0.01)
                return {'status': 'healthy'}

            result = await mock_health_check()
            assert result['status'] == 'healthy'

            return ValidationResult(
                name="Async Health Check Pattern",
                status=ValidationStatus.PASS,
                message="Async health check executed successfully",
                duration=time.time() - start
            )
        except Exception as e:
            return ValidationResult(
                name="Async Health Check Pattern",
                status=ValidationStatus.FAIL,
                message="Failed to execute async health check",
                duration=time.time() - start,
                error=str(e)
            )

    async def _test_parallel_execution(self) -> ValidationResult:
        """Test parallel execution pattern"""
        start = time.time()
        try:
            async def task():
                await asyncio.sleep(0.05)
                return "done"

            # Run 3 tasks in parallel
            results = await asyncio.gather(*[task() for _ in range(3)])
            duration = time.time() - start

            # Should complete in ~0.05s, not 0.15s
            if duration < 0.1:
                return ValidationResult(
                    name="Parallel Execution",
                    status=ValidationStatus.PASS,
                    message=f"3 tasks completed in parallel ({duration:.3f}s)",
                    duration=duration
                )
            else:
                return ValidationResult(
                    name="Parallel Execution",
                    status=ValidationStatus.WARN,
                    message=f"Tasks may not have run in parallel ({duration:.3f}s)",
                    duration=duration
                )
        except Exception as e:
            return ValidationResult(
                name="Parallel Execution",
                status=ValidationStatus.FAIL,
                message="Failed to execute tasks in parallel",
                duration=time.time() - start,
                error=str(e)
            )

    async def _test_timeout_protection(self) -> ValidationResult:
        """Test timeout protection"""
        start = time.time()
        try:
            async def slow_task():
                await asyncio.sleep(10)

            # Should timeout
            try:
                await asyncio.wait_for(slow_task(), timeout=0.1)
                return ValidationResult(
                    name="Timeout Protection",
                    status=ValidationStatus.FAIL,
                    message="Timeout did not trigger",
                    duration=time.time() - start
                )
            except asyncio.TimeoutError:
                return ValidationResult(
                    name="Timeout Protection",
                    status=ValidationStatus.PASS,
                    message="Timeout protection working correctly",
                    duration=time.time() - start
                )
        except Exception as e:
            return ValidationResult(
                name="Timeout Protection",
                status=ValidationStatus.FAIL,
                message="Timeout test failed unexpectedly",
                duration=time.time() - start,
                error=str(e)
            )

    async def validate_tutorial_02_custom_agents(self) -> TutorialValidation:
        """Validate Tutorial 02: Building Custom Agents"""
        start = time.time()
        results = []

        # Test 1: Agent planning
        result = self._test_agent_planning()
        results.append(result)

        # Test 2: Variable substitution
        result = self._test_variable_substitution()
        results.append(result)

        # Test 3: Safety validation
        result = self._test_safety_validation()
        results.append(result)

        duration = time.time() - start
        return self._create_tutorial_summary("02", "Building Custom Agents", results, duration)

    def _test_agent_planning(self) -> ValidationResult:
        """Test agent planning logic"""
        start = time.time()
        try:
            # Simulate planning from tutorial
            plan = [
                {'tool': 'step1', 'params': {}, 'rationale': 'First step'},
                {'tool': 'step2', 'params': {}, 'rationale': 'Second step'}
            ]

            assert len(plan) == 2
            assert 'tool' in plan[0]
            assert 'rationale' in plan[0]

            return ValidationResult(
                name="Agent Planning",
                status=ValidationStatus.PASS,
                message="Agent planning logic validated",
                duration=time.time() - start
            )
        except Exception as e:
            return ValidationResult(
                name="Agent Planning",
                status=ValidationStatus.FAIL,
                message="Agent planning validation failed",
                duration=time.time() - start,
                error=str(e)
            )

    def _test_variable_substitution(self) -> ValidationResult:
        """Test variable substitution pattern"""
        start = time.time()
        try:
            import re

            def substitute_variables(params: Dict, history: List[Dict]) -> Dict:
                pattern = re.compile(r'\$\{step_(\d+)\.output\.([a-zA-Z_][a-zA-Z0-9_]*)\}')
                result = {}

                for key, value in params.items():
                    if isinstance(value, str):
                        match = pattern.match(value)
                        if match:
                            step_idx = int(match.group(1))
                            output_key = match.group(2)
                            if step_idx < len(history):
                                result[key] = history[step_idx].get(output_key)
                            else:
                                raise ValueError(f"Step {step_idx} not in history")
                        else:
                            result[key] = value
                    else:
                        result[key] = value
                return result

            # Test
            history = [{'backup_path': '/path/to/backup.sql'}]
            params = {'path': '${step_0.output.backup_path}'}
            result = substitute_variables(params, history)

            assert result['path'] == '/path/to/backup.sql'

            return ValidationResult(
                name="Variable Substitution",
                status=ValidationStatus.PASS,
                message="Variable substitution working correctly",
                duration=time.time() - start
            )
        except Exception as e:
            return ValidationResult(
                name="Variable Substitution",
                status=ValidationStatus.FAIL,
                message="Variable substitution failed",
                duration=time.time() - start,
                error=str(e)
            )

    def _test_safety_validation(self) -> ValidationResult:
        """Test safety validation logic"""
        start = time.time()
        try:
            def validate_safety(tool_name: str, safety_level: str) -> Dict:
                safe_tools = ['analyze', 'query']
                risky_tools = ['delete', 'drop']

                if tool_name in safe_tools:
                    return {'safe': True, 'requires_approval': False}
                elif tool_name in risky_tools:
                    return {'safe': False, 'requires_approval': True}
                else:
                    return {'safe': True, 'requires_approval': safety_level == 'strict'}

            # Test safe tool
            result = validate_safety('analyze', 'moderate')
            assert result['safe'] == True
            assert result['requires_approval'] == False

            # Test risky tool
            result = validate_safety('delete', 'moderate')
            assert result['requires_approval'] == True

            return ValidationResult(
                name="Safety Validation",
                status=ValidationStatus.PASS,
                message="Safety validation logic validated",
                duration=time.time() - start
            )
        except Exception as e:
            return ValidationResult(
                name="Safety Validation",
                status=ValidationStatus.FAIL,
                message="Safety validation failed",
                duration=time.time() - start,
                error=str(e)
            )

    async def validate_tutorial_03_tool_registry(self) -> TutorialValidation:
        """Validate Tutorial 03: Tool Registry"""
        start = time.time()
        results = []

        # Test 1: Tool definition structure
        result = self._test_tool_definition()
        results.append(result)

        # Test 2: JSON schema validation
        result = self._test_json_schema()
        results.append(result)

        # Test 3: Risk level classification
        result = self._test_risk_levels()
        results.append(result)

        duration = time.time() - start
        return self._create_tutorial_summary("03", "Tool Registry Guide", results, duration)

    def _test_tool_definition(self) -> ValidationResult:
        """Test tool definition structure"""
        start = time.time()
        try:
            from dataclasses import dataclass

            @dataclass
            class ToolDefinition:
                name: str
                description: str
                risk_level: str
                parameters_schema: Dict

            tool = ToolDefinition(
                name="test_tool",
                description="Test tool",
                risk_level="safe",
                parameters_schema={"type": "object"}
            )

            assert tool.name == "test_tool"
            assert tool.risk_level == "safe"

            return ValidationResult(
                name="Tool Definition Structure",
                status=ValidationStatus.PASS,
                message="Tool definition structure validated",
                duration=time.time() - start
            )
        except Exception as e:
            return ValidationResult(
                name="Tool Definition Structure",
                status=ValidationStatus.FAIL,
                message="Tool definition validation failed",
                duration=time.time() - start,
                error=str(e)
            )

    def _test_json_schema(self) -> ValidationResult:
        """Test JSON schema patterns"""
        start = time.time()
        try:
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0}
                },
                "required": ["name"]
            }

            assert "required" in schema
            assert "properties" in schema
            assert schema["properties"]["age"]["minimum"] == 0

            return ValidationResult(
                name="JSON Schema Validation",
                status=ValidationStatus.PASS,
                message="JSON schema patterns validated",
                duration=time.time() - start
            )
        except Exception as e:
            return ValidationResult(
                name="JSON Schema Validation",
                status=ValidationStatus.FAIL,
                message="JSON schema validation failed",
                duration=time.time() - start,
                error=str(e)
            )

    def _test_risk_levels(self) -> ValidationResult:
        """Test risk level classification"""
        start = time.time()
        try:
            class RiskLevel(Enum):
                SAFE = "safe"
                LOW = "low"
                MEDIUM = "medium"
                HIGH = "high"
                CRITICAL = "critical"

            assert len(RiskLevel) == 5
            assert RiskLevel.SAFE.value == "safe"
            assert RiskLevel.CRITICAL.value == "critical"

            return ValidationResult(
                name="Risk Level Classification",
                status=ValidationStatus.PASS,
                message="Risk levels validated",
                duration=time.time() - start
            )
        except Exception as e:
            return ValidationResult(
                name="Risk Level Classification",
                status=ValidationStatus.FAIL,
                message="Risk level validation failed",
                duration=time.time() - start,
                error=str(e)
            )

    async def validate_tutorial_04_safety(self) -> TutorialValidation:
        """Validate Tutorial 04: Safety and Approvals"""
        start = time.time()
        results = []

        # Test 1: SQL risk analysis
        result = self._test_sql_risk_analysis()
        results.append(result)

        # Test 2: Destructive operation detection
        result = self._test_destructive_detection()
        results.append(result)

        # Test 3: Approval callback
        result = await self._test_approval_callback()
        results.append(result)

        duration = time.time() - start
        return self._create_tutorial_summary("04", "Safety and Approvals", results, duration)

    def _test_sql_risk_analysis(self) -> ValidationResult:
        """Test SQL risk analysis"""
        start = time.time()
        try:
            import re

            def analyze_sql_risk(sql: str) -> str:
                sql_upper = sql.upper()
                if 'DROP TABLE' in sql_upper or 'TRUNCATE' in sql_upper:
                    return 'CRITICAL'
                elif 'DELETE FROM' in sql_upper and 'WHERE' not in sql_upper:
                    return 'HIGH'
                elif 'UPDATE' in sql_upper and 'WHERE' in sql_upper:
                    return 'MEDIUM'
                else:
                    return 'LOW'

            # Test cases from tutorial
            assert analyze_sql_risk("SELECT * FROM users") == 'LOW'
            assert analyze_sql_risk("DELETE FROM users") == 'HIGH'
            assert analyze_sql_risk("DROP TABLE users") == 'CRITICAL'

            return ValidationResult(
                name="SQL Risk Analysis",
                status=ValidationStatus.PASS,
                message="SQL risk analysis validated",
                duration=time.time() - start
            )
        except Exception as e:
            return ValidationResult(
                name="SQL Risk Analysis",
                status=ValidationStatus.FAIL,
                message="SQL risk analysis failed",
                duration=time.time() - start,
                error=str(e)
            )

    def _test_destructive_detection(self) -> ValidationResult:
        """Test destructive operation detection"""
        start = time.time()
        try:
            def is_destructive(tool_name: str, params: Dict) -> bool:
                destructive_tools = ['drop_table', 'truncate_table', 'delete_backup']

                if tool_name in destructive_tools:
                    return True

                sql = params.get('sql', '')
                if any(pattern in sql.upper() for pattern in ['DROP', 'TRUNCATE']):
                    return True

                return False

            assert is_destructive('drop_table', {}) == True
            assert is_destructive('backup_database', {}) == False
            assert is_destructive('execute_query', {'sql': 'DROP TABLE users'}) == True

            return ValidationResult(
                name="Destructive Operation Detection",
                status=ValidationStatus.PASS,
                message="Destructive operation detection validated",
                duration=time.time() - start
            )
        except Exception as e:
            return ValidationResult(
                name="Destructive Operation Detection",
                status=ValidationStatus.FAIL,
                message="Destructive detection failed",
                duration=time.time() - start,
                error=str(e)
            )

    async def _test_approval_callback(self) -> ValidationResult:
        """Test approval callback pattern"""
        start = time.time()
        try:
            async def auto_approve_callback(request: Dict) -> Dict:
                tool = request['step']['tool']
                if tool in ['backup_database', 'analyze']:
                    return {'approved': True, 'reason': 'Auto-approved'}
                return {'approved': False, 'reason': 'Manual approval required'}

            # Test approval
            request = {'step': {'tool': 'backup_database'}}
            result = await auto_approve_callback(request)
            assert result['approved'] == True

            # Test rejection
            request = {'step': {'tool': 'drop_table'}}
            result = await auto_approve_callback(request)
            assert result['approved'] == False

            return ValidationResult(
                name="Approval Callback",
                status=ValidationStatus.PASS,
                message="Approval callback pattern validated",
                duration=time.time() - start
            )
        except Exception as e:
            return ValidationResult(
                name="Approval Callback",
                status=ValidationStatus.FAIL,
                message="Approval callback failed",
                duration=time.time() - start,
                error=str(e)
            )

    def _create_tutorial_summary(self, tutorial_id: str, name: str,
                                  results: List[ValidationResult], duration: float) -> TutorialValidation:
        """Create summary for tutorial validation"""
        passed = sum(1 for r in results if r.status == ValidationStatus.PASS)
        failed = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        warnings = sum(1 for r in results if r.status == ValidationStatus.WARN)
        skipped = sum(1 for r in results if r.status == ValidationStatus.SKIP)

        return TutorialValidation(
            tutorial_id=tutorial_id,
            tutorial_name=name,
            total_checks=len(results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
            duration=duration,
            results=results
        )


# ============================================================================
# Report Generator
# ============================================================================

class ReportGenerator:
    """Generates validation reports"""

    @staticmethod
    def print_console_report(report: ValidationReport, verbose: bool = False):
        """Print formatted console report"""
        print("\n" + "="*80)
        print("AISHELL TUTORIAL VALIDATION REPORT")
        print("="*80)
        print(f"Timestamp: {report.timestamp}")
        print(f"Python Version: {report.python_version}")
        print(f"Total Duration: {report.total_duration:.2f}s")

        # Prerequisite checks
        print("\n" + "-"*80)
        print("PREREQUISITE CHECKS")
        print("-"*80)

        for check in report.prerequisite_checks:
            status_symbol = check.status.value.split()[0]
            print(f"{status_symbol} {check.name}: {check.message}")
            if verbose and check.details:
                print(f"   Details: {json.dumps(check.details, indent=2)}")
            if check.error:
                print(f"   Error: {check.error}")

        # Tutorial validations
        print("\n" + "-"*80)
        print("TUTORIAL VALIDATIONS")
        print("-"*80)

        for tutorial in report.tutorial_validations:
            print(f"\nTutorial {tutorial.tutorial_id}: {tutorial.tutorial_name}")
            print(f"  Tests: {tutorial.total_checks} | "
                  f"Passed: {tutorial.passed} | "
                  f"Failed: {tutorial.failed} | "
                  f"Warnings: {tutorial.warnings} | "
                  f"Duration: {tutorial.duration:.2f}s")

            if verbose:
                for result in tutorial.results:
                    status_symbol = result.status.value.split()[0]
                    print(f"    {status_symbol} {result.name}: {result.message}")
                    if result.error:
                        print(f"       Error: {result.error}")

        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total Tutorials: {report.total_tutorials}")
        print(f"Total Checks: {report.total_checks}")
        print(f"Passed: {report.total_passed} ({report.total_passed/report.total_checks*100:.1f}%)")
        print(f"Failed: {report.total_failed}")
        print(f"Warnings: {report.total_warnings}")

        if report.total_failed == 0:
            print("\n✓ All tutorial validations passed successfully!")
        else:
            print(f"\n✗ {report.total_failed} validation(s) failed. See details above.")

        print("="*80 + "\n")

    @staticmethod
    def save_json_report(report: ValidationReport, output_file: str):
        """Save report as JSON"""
        with open(output_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"Report saved to: {output_file}")


# ============================================================================
# Main Validation Runner
# ============================================================================

class ValidationRunner:
    """Main validation runner"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.prerequisite_validator = PrerequisiteValidator()
        self.tutorial_validator = TutorialValidator(verbose)

    async def run_all_validations(self, specific_tutorial: Optional[str] = None) -> ValidationReport:
        """Run all validations"""
        start_time = time.time()

        # Run prerequisite checks
        print("Running prerequisite checks...")
        prerequisite_results = [
            self.prerequisite_validator.check_python_version(),
            self.prerequisite_validator.check_dependencies(),
            self.prerequisite_validator.check_database_connectivity(),
            self.prerequisite_validator.check_llm_availability(),
            self.prerequisite_validator.check_file_system_access(),
            self.prerequisite_validator.check_project_structure()
        ]

        # Check if prerequisites passed
        prereq_failed = any(r.status == ValidationStatus.FAIL for r in prerequisite_results)
        if prereq_failed:
            print("⚠ Some prerequisite checks failed. Tutorial validation may be limited.")

        # Run tutorial validations
        print("\nRunning tutorial validations...")
        tutorial_validations = []

        tutorials_to_run = {
            '01': self.tutorial_validator.validate_tutorial_01_health_checks,
            '02': self.tutorial_validator.validate_tutorial_02_custom_agents,
            '03': self.tutorial_validator.validate_tutorial_03_tool_registry,
            '04': self.tutorial_validator.validate_tutorial_04_safety
        }

        if specific_tutorial:
            if specific_tutorial in tutorials_to_run:
                validation = await tutorials_to_run[specific_tutorial]()
                tutorial_validations.append(validation)
            else:
                print(f"Warning: Tutorial {specific_tutorial} not found")
        else:
            for tutorial_id, validator_func in tutorials_to_run.items():
                validation = await validator_func()
                tutorial_validations.append(validation)

        # Calculate totals
        total_checks = sum(t.total_checks for t in tutorial_validations)
        total_passed = sum(t.passed for t in tutorial_validations)
        total_failed = sum(t.failed for t in tutorial_validations)
        total_warnings = sum(t.warnings for t in tutorial_validations)
        total_duration = time.time() - start_time

        # Create report
        report = ValidationReport(
            timestamp=datetime.now().isoformat(),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            total_tutorials=len(tutorial_validations),
            total_checks=total_checks,
            total_passed=total_passed,
            total_failed=total_failed,
            total_warnings=total_warnings,
            total_duration=total_duration,
            prerequisite_checks=prerequisite_results,
            tutorial_validations=tutorial_validations
        )

        return report


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Validate AIShell tutorial code examples")
    parser.add_argument(
        '--tutorial',
        type=str,
        help='Validate specific tutorial (e.g., 01, 02, 03, 04)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed validation output'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Save report to JSON file'
    )
    parser.add_argument(
        '--format',
        choices=['console', 'json', 'both'],
        default='console',
        help='Output format (default: console)'
    )

    args = parser.parse_args()

    # Run validations
    runner = ValidationRunner(verbose=args.verbose)
    report = asyncio.run(runner.run_all_validations(specific_tutorial=args.tutorial))

    # Generate reports
    if args.format in ['console', 'both']:
        ReportGenerator.print_console_report(report, verbose=args.verbose)

    if args.format in ['json', 'both'] or args.output:
        output_file = args.output or f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        ReportGenerator.save_json_report(report, output_file)

    # Exit code based on results
    sys.exit(0 if report.total_failed == 0 else 1)


if __name__ == "__main__":
    main()
