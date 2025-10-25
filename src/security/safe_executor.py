"""
Safe Command Executor

Prevents command injection vulnerabilities by providing a secure
interface for executing system commands.

Security: CRITICAL
CVSS: 9.8 (Critical) - Prevents arbitrary code execution
CWE: CWE-78 (OS Command Injection)
"""

import shlex
import subprocess
import os
from typing import List, Optional, Dict, Any
from pathlib import Path


class SecurityError(Exception):
    """Raised when a security violation is detected"""
    pass


class SafeCommandExecutor:
    """
    Secure command execution without shell injection vulnerabilities

    This class provides a safe interface for executing system commands
    by never using shell=True and validating all inputs.

    Example:
        executor = SafeCommandExecutor()
        result = executor.execute_safe('ls', ['-la', '/home'])
        print(result.stdout)
    """

    # Whitelist of allowed commands
    # Customize this based on your application's needs
    ALLOWED_COMMANDS = {
        'ls', 'pwd', 'echo', 'cat', 'grep', 'find', 'wc',
        'head', 'tail', 'sort', 'uniq', 'cut', 'sed', 'awk',
        'git', 'python3', 'pip3', 'pytest', 'mypy',
        'docker', 'kubectl', 'npm', 'node',
    }

    # Commands that should NEVER be allowed
    BLACKLISTED_COMMANDS = {
        'rm', 'rmdir', 'del', 'delete', 'format',
        'dd', 'fdisk', 'mkfs', 'shutdown', 'reboot',
        'kill', 'killall', 'pkill',
        'chmod', 'chown', 'chgrp',  # Unless specifically needed
        'sudo', 'su',
        'eval', 'exec',
    }

    # Dangerous argument patterns
    DANGEROUS_PATTERNS = [
        ';', '&&', '||', '|', '>', '>>', '<', '`',
        '$(',  '${', '\n', '\r',
    ]

    def __init__(self, allowed_commands: Optional[set] = None):
        """
        Initialize safe executor

        Args:
            allowed_commands: Custom set of allowed commands (optional)
                            If None, uses default whitelist
        """
        if allowed_commands is not None:
            self.allowed_commands = allowed_commands
        else:
            self.allowed_commands = self.ALLOWED_COMMANDS.copy()

    def execute_safe(
        self,
        command: str,
        args: Optional[List[str]] = None,
        timeout: int = 30,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> subprocess.CompletedProcess:
        """
        Execute command safely without shell injection

        Args:
            command: Command name (must be whitelisted)
            args: List of arguments (will be properly escaped)
            timeout: Command timeout in seconds (default: 30)
            cwd: Working directory (validated)
            env: Environment variables (validated)

        Returns:
            CompletedProcess with stdout, stderr, and returncode

        Raises:
            SecurityError: If command not whitelisted or unsafe arguments detected
            subprocess.TimeoutExpired: If command exceeds timeout
        """
        if args is None:
            args = []

        # Validate command
        self._validate_command(command)

        # Validate arguments
        self._validate_arguments(args)

        # Validate working directory
        if cwd is not None:
            cwd = self._validate_path(cwd)

        # Validate environment
        if env is not None:
            env = self._validate_environment(env)

        # Build command list (NEVER use shell=True)
        cmd_list = [command] + args

        try:
            # Execute without shell
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=env,
                check=False,  # Don't raise on non-zero exit
                shell=False,  # CRITICAL: Never True!
            )

            return result

        except subprocess.TimeoutExpired as e:
            raise SecurityError(f"Command timed out after {timeout} seconds") from e
        except FileNotFoundError as e:
            raise SecurityError(f"Command not found: {command}") from e
        except Exception as e:
            raise SecurityError(f"Command execution failed: {e}") from e

    def _validate_command(self, command: str) -> None:
        """
        Validate that command is allowed

        Args:
            command: Command name to validate

        Raises:
            SecurityError: If command is not allowed
        """
        # Check blacklist first
        if command in self.BLACKLISTED_COMMANDS:
            raise SecurityError(
                f"Command '{command}' is blacklisted and cannot be executed"
            )

        # Check whitelist
        if command not in self.allowed_commands:
            raise SecurityError(
                f"Command '{command}' is not in whitelist. "
                f"Allowed commands: {sorted(self.allowed_commands)}"
            )

        # Additional validation
        if not command.isalnum() and command not in self.allowed_commands:
            raise SecurityError(f"Command contains invalid characters: {command}")

    def _validate_arguments(self, args: List[str]) -> None:
        """
        Validate command arguments for injection attempts

        Args:
            args: List of arguments to validate

        Raises:
            SecurityError: If dangerous patterns detected
        """
        for arg in args:
            # Check for shell metacharacters
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern in arg:
                    raise SecurityError(
                        f"Argument contains dangerous pattern '{pattern}': {arg}"
                    )

            # Check for null bytes
            if '\x00' in arg:
                raise SecurityError("Argument contains null byte")

    @staticmethod
    def sanitize_path(path: str, base_dir: Optional[str] = None) -> str:
        """
        Sanitize file path to prevent directory traversal

        Args:
            path: Path to sanitize
            base_dir: Base directory to restrict to (optional)

        Returns:
            Sanitized absolute path

        Raises:
            SecurityError: If path traversal detected
        """
        # Normalize path
        clean_path = os.path.normpath(path)

        # Convert to absolute path
        if base_dir:
            base = Path(base_dir).resolve()
            full_path = (base / clean_path).resolve()
        else:
            base = Path.cwd()
            full_path = Path(clean_path).resolve()

        # Ensure path doesn't escape base directory
        if base_dir and not str(full_path).startswith(str(base)):
            raise SecurityError(
                f"Path traversal detected: {path} escapes {base_dir}"
            )

        # Check for suspicious patterns
        if '..' in Path(path).parts:
            raise SecurityError(f"Path contains '..' component: {path}")

        return str(full_path)

    def _validate_path(self, path: str) -> str:
        """
        Validate and sanitize working directory path

        Args:
            path: Path to validate

        Returns:
            Validated absolute path

        Raises:
            SecurityError: If path is invalid or doesn't exist
        """
        clean_path = self.sanitize_path(path)

        if not os.path.exists(clean_path):
            raise SecurityError(f"Path does not exist: {path}")

        if not os.path.isdir(clean_path):
            raise SecurityError(f"Path is not a directory: {path}")

        return clean_path

    @staticmethod
    def _validate_environment(env: Dict[str, str]) -> Dict[str, str]:
        """
        Validate environment variables

        Args:
            env: Environment variables dictionary

        Returns:
            Validated environment dictionary

        Raises:
            SecurityError: If dangerous environment variables detected
        """
        # Check for dangerous variables that could affect execution
        dangerous_vars = {
            'LD_PRELOAD', 'LD_LIBRARY_PATH', 'PATH', 'PYTHONPATH',
            'IFS', 'BASH_ENV', 'ENV',
        }

        for var in dangerous_vars:
            if var in env:
                raise SecurityError(
                    f"Setting environment variable '{var}' is not allowed"
                )

        # Validate variable names (must be valid identifiers)
        for key in env.keys():
            if not key.replace('_', '').isalnum():
                raise SecurityError(f"Invalid environment variable name: {key}")

        return env


class SafePythonExecutor(SafeCommandExecutor):
    """
    Specialized executor for safe Python code execution

    Prevents eval() and exec() vulnerabilities by using AST parsing
    and whitelisting instead.
    """

    def __init__(self):
        super().__init__(allowed_commands={'python3'})

    def evaluate_expression(self, expr: str) -> Any:
        """
        Safely evaluate mathematical expressions only

        Args:
            expr: Expression to evaluate (must be safe math only)

        Returns:
            Result of expression

        Raises:
            SecurityError: If expression contains unsafe operations
        """
        import ast

        try:
            # Parse expression
            tree = ast.parse(expr, mode='eval')

            # Whitelist of allowed node types
            allowed_nodes = {
                ast.Expression, ast.BinOp, ast.UnaryOp,
                ast.Num, ast.Constant,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
                ast.USub, ast.UAdd,
            }

            # Walk the AST and check all nodes
            for node in ast.walk(tree):
                if type(node) not in allowed_nodes:
                    raise SecurityError(
                        f"Unsafe operation in expression: {type(node).__name__}"
                    )

            # Safe to evaluate
            return eval(compile(tree, filename='<ast>', mode='eval'))

        except SyntaxError as e:
            raise SecurityError(f"Invalid expression syntax: {e}") from e
        except Exception as e:
            raise SecurityError(f"Expression evaluation failed: {e}") from e


# Example usage
if __name__ == "__main__":
    print("=== Testing Safe Command Executor ===\n")

    executor = SafeCommandExecutor()

    # Test 1: Safe command
    print("Test 1: Safe command (ls)")
    try:
        result = executor.execute_safe('ls', ['-la'])
        print(f"✅ SUCCESS: {len(result.stdout)} bytes output\n")
    except SecurityError as e:
        print(f"❌ FAILED: {e}\n")

    # Test 2: Blocked command
    print("Test 2: Blacklisted command (rm)")
    try:
        result = executor.execute_safe('rm', ['-rf', '/'])
        print(f"❌ FAILED: Command should have been blocked!\n")
    except SecurityError as e:
        print(f"✅ BLOCKED: {e}\n")

    # Test 3: Command injection attempt
    print("Test 3: Command injection (with semicolon)")
    try:
        result = executor.execute_safe('echo', ['test; rm -rf /'])
        print(f"❌ FAILED: Injection should have been blocked!\n")
    except SecurityError as e:
        print(f"✅ BLOCKED: {e}\n")

    # Test 4: Path traversal
    print("Test 4: Path traversal")
    try:
        path = executor.sanitize_path('../../../etc/passwd')
        print(f"❌ FAILED: Path traversal should have been blocked!\n")
    except SecurityError as e:
        print(f"✅ BLOCKED: {e}\n")

    # Test 5: Safe Python expression
    print("Test 5: Safe math expression")
    py_executor = SafePythonExecutor()
    try:
        result = py_executor.evaluate_expression('2 + 2 * 3')
        print(f"✅ SUCCESS: 2 + 2 * 3 = {result}\n")
    except SecurityError as e:
        print(f"❌ FAILED: {e}\n")

    # Test 6: Unsafe Python expression
    print("Test 6: Unsafe Python expression (eval)")
    try:
        result = py_executor.evaluate_expression('__import__("os").system("ls")')
        print(f"❌ FAILED: Should have been blocked!\n")
    except SecurityError as e:
        print(f"✅ BLOCKED: {e}\n")

    print("=== All tests completed ===")
