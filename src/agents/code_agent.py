"""
Code Agent - Generates and analyzes code

Specialized agent for code generation, refactoring, analysis,
and programming tasks.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List

from src.agents.base import BaseAgent, AgentCapability, TaskContext

logger = logging.getLogger(__name__)


class CodeAgent(BaseAgent):
    """
    Agent specialized in code generation and analysis

    Features:
    - Code generation from specifications
    - Code refactoring and optimization
    - Bug detection and fixing
    - Documentation generation
    - Code review and quality checks
    """

    def __init__(self, agent_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(agent_id=agent_id, config=config, **kwargs)
        self.generated_code: List[Dict[str, Any]] = []
        self.supported_languages = config.get(
            "languages", ["python", "javascript", "sql", "bash"]
        )

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create code task execution plan

        Args:
            task: Task context with code requirements

        Returns:
            List of planned code steps
        """
        task_type = task.input_data.get("type", "generate")
        language = task.input_data.get("language", "python")
        specification = task.input_data.get("specification", "")

        if language not in self.supported_languages:
            raise ValueError(f"Language '{language}' not supported")

        plan = []

        if task_type == "generate":
            # Code generation workflow
            plan.extend(
                [
                    {
                        "tool": "analyze_requirements",
                        "params": {"specification": specification},
                        "rationale": "Analyze code requirements and constraints",
                    },
                    {
                        "tool": "generate_code",
                        "params": {
                            "language": language,
                            "specification": specification,
                            "style": task.input_data.get("style", "standard"),
                        },
                        "rationale": f"Generate {language} code from specification",
                    },
                    {
                        "tool": "validate_code",
                        "params": {"language": language},
                        "rationale": "Validate generated code syntax and quality",
                    },
                ]
            )

        elif task_type == "refactor":
            # Code refactoring workflow
            code = task.input_data.get("code", "")
            plan.extend(
                [
                    {
                        "tool": "analyze_code",
                        "params": {"code": code, "language": language},
                        "rationale": "Analyze code structure and identify improvements",
                    },
                    {
                        "tool": "refactor_code",
                        "params": {
                            "code": code,
                            "improvements": task.input_data.get("improvements", []),
                        },
                        "rationale": "Refactor code with improvements",
                    },
                ]
            )

        elif task_type == "analyze":
            # Code analysis workflow
            code = task.input_data.get("code", "")
            plan.append(
                {
                    "tool": "analyze_code",
                    "params": {
                        "code": code,
                        "language": language,
                        "checks": task.input_data.get(
                            "checks", ["complexity", "quality", "bugs"]
                        ),
                    },
                    "rationale": "Perform comprehensive code analysis",
                }
            )

        else:
            raise ValueError(f"Unknown code task type: {task_type}")

        return plan

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a code step

        Args:
            step: Step definition

        Returns:
            Step execution result
        """
        tool = step["tool"]
        params = step["params"]

        if tool == "analyze_requirements":
            return await self._analyze_requirements(params)
        elif tool == "generate_code":
            return await self._generate_code(params)
        elif tool == "validate_code":
            return await self._validate_code(params)
        elif tool == "analyze_code":
            return await self._analyze_code(params)
        elif tool == "refactor_code":
            return await self._refactor_code(params)
        else:
            raise ValueError(f"Unknown code tool: {tool}")

    async def _analyze_requirements(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code requirements"""
        specification = params["specification"]

        logger.info("Analyzing code requirements...")

        # Use LLM to analyze requirements
        if self.llm_manager and hasattr(self.llm_manager, "explain_query"):
            analysis = self.llm_manager.explain_query(
                f"Analyze these code requirements: {specification}"
            )
        else:
            analysis = f"Requirements: {specification}"

        return {
            "specification": specification,
            "analysis": analysis,
            "complexity": "medium",  # Simplified
            "estimated_lines": 50,
        }

    async def _generate_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code from specification"""
        language = params["language"]
        specification = params["specification"]
        style = params.get("style", "standard")

        logger.info(f"Generating {language} code...")

        # In a real implementation, use LLM to generate code
        # For now, generate template code
        if language == "python":
            code = self._generate_python_template(specification)
        elif language == "javascript":
            code = self._generate_js_template(specification)
        elif language == "sql":
            code = self._generate_sql_template(specification)
        else:
            code = f"# Generated {language} code\n# Specification: {specification}\n"

        result = {
            "language": language,
            "code": code,
            "lines": len(code.split("\n")),
            "style": style,
        }

        self.generated_code.append(result)

        return result

    def _generate_python_template(self, specification: str) -> str:
        """Generate Python code template"""
        return f'''"""
{specification}
"""

def main():
    """Main function"""
    # TODO: Implement functionality
    pass


if __name__ == "__main__":
    main()
'''

    def _generate_js_template(self, specification: str) -> str:
        """Generate JavaScript code template"""
        return f'''/**
 * {specification}
 */

function main() {{
    // TODO: Implement functionality
}}

main();
'''

    def _generate_sql_template(self, specification: str) -> str:
        """Generate SQL code template"""
        return f'''-- {specification}

SELECT *
FROM table_name
WHERE condition = true;
'''

    async def _validate_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate code syntax and quality"""
        language = params["language"]

        if not self.generated_code:
            return {"valid": False, "errors": ["No code to validate"]}

        code = self.generated_code[-1]["code"]

        logger.info(f"Validating {language} code...")

        # Basic validation (in real implementation, use proper parsers/linters)
        errors = []
        warnings = []

        # Check for basic syntax patterns
        if language == "python":
            if "def " not in code and "class " not in code:
                warnings.append("No functions or classes defined")
        elif language == "javascript":
            if "function " not in code and "const " not in code:
                warnings.append("No functions or constants defined")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "quality_score": 0.8 if len(errors) == 0 else 0.4,
        }

    async def _analyze_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code quality and complexity"""
        code = params["code"]
        language = params["language"]
        checks = params.get("checks", ["complexity", "quality"])

        logger.info(f"Analyzing {language} code...")

        lines = code.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        analysis = {
            "language": language,
            "total_lines": len(lines),
            "code_lines": len(non_empty_lines),
            "complexity": "medium",  # Simplified
            "quality_score": 0.75,
            "issues": [],
        }

        # Basic checks
        if "complexity" in checks:
            # Simplified complexity analysis
            nesting_level = max(
                (len(line) - len(line.lstrip())) // 4 for line in lines
            )
            analysis["cyclomatic_complexity"] = nesting_level
            if nesting_level > 5:
                analysis["issues"].append("High nesting level detected")

        if "quality" in checks:
            # Check for comments
            comment_lines = [
                line for line in lines if line.strip().startswith("#")
                or line.strip().startswith("//")
            ]
            if len(comment_lines) < len(non_empty_lines) * 0.1:
                analysis["issues"].append("Low comment density")

        if "bugs" in checks:
            # Basic bug patterns
            if "TODO" in code or "FIXME" in code:
                analysis["issues"].append("TODO/FIXME markers found")

        return analysis

    async def _refactor_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Refactor code with improvements"""
        code = params["code"]
        improvements = params.get("improvements", [])

        logger.info("Refactoring code...")

        refactored = code

        # Apply basic improvements
        for improvement in improvements:
            if improvement == "add_comments":
                # Add basic comments (simplified)
                lines = refactored.split("\n")
                refactored = "# Refactored code\n" + "\n".join(lines)
            elif improvement == "format":
                # Basic formatting
                refactored = refactored.strip() + "\n"

        return {
            "original_lines": len(code.split("\n")),
            "refactored_lines": len(refactored.split("\n")),
            "improvements_applied": improvements,
            "code": refactored,
        }

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate code step safety

        Args:
            step: Step to validate

        Returns:
            Safety validation result
        """
        tool = step["tool"]
        params = step["params"]

        # Code analysis is safe, code generation might need review
        if tool == "generate_code":
            return {
                "requires_approval": False,
                "safe": True,
                "risk_level": "low",
                "risks": ["Generated code should be reviewed before execution"],
                "mitigations": ["Code review", "Testing"],
            }

        return {
            "requires_approval": False,
            "safe": True,
            "risk_level": "low",
            "risks": [],
            "mitigations": [],
        }

    def get_generated_code(self) -> List[Dict[str, Any]]:
        """Get all generated code"""
        return self.generated_code

    def clear_code(self) -> None:
        """Clear generated code history"""
        self.generated_code.clear()
