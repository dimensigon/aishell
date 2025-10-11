"""
Secure Error Handling

Provides secure error handling that prevents information leakage in production.
"""

import logging
import traceback
import sys
from typing import Optional, Type, Any
from functools import wraps
import os


# Check if running in debug mode
DEBUG_MODE = os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes')
PRODUCTION_MODE = os.environ.get('PRODUCTION', '').lower() in ('true', '1', 'yes')


class SecurityError(Exception):
    """Security-related error"""
    pass


class SecureErrorHandler:
    """
    Secure error handler that prevents information disclosure.

    Features:
    - Generic error messages in production
    - Detailed logging for debugging
    - Stack trace suppression in production
    - Sensitive data filtering
    """

    # Sensitive keywords to filter from error messages
    SENSITIVE_KEYWORDS = [
        'password',
        'passwd',
        'secret',
        'token',
        'key',
        'api_key',
        'apikey',
        'credential',
        'auth',
        'session',
        'cookie',
    ]

    @staticmethod
    def sanitize_error_message(message: str) -> str:
        """
        Remove sensitive information from error message.

        Args:
            message: Original error message

        Returns:
            Sanitized error message
        """
        # Convert to lowercase for comparison
        message_lower = message.lower()

        # Check for sensitive keywords
        for keyword in SecureErrorHandler.SENSITIVE_KEYWORDS:
            if keyword in message_lower:
                # Mask the sensitive information
                parts = message.split('=')
                if len(parts) > 1:
                    # Replace value after '=' with asterisks
                    return parts[0] + '=***'

        return message

    @staticmethod
    def format_error_for_user(
        error: Exception,
        default_message: str = "An error occurred"
    ) -> str:
        """
        Format error message for user display.

        Args:
            error: Exception object
            default_message: Default message if error is sensitive

        Returns:
            User-friendly error message
        """
        if PRODUCTION_MODE and not DEBUG_MODE:
            # Production: Generic error message
            return default_message
        else:
            # Development: Show actual error
            error_msg = str(error)
            return SecureErrorHandler.sanitize_error_message(error_msg)

    @staticmethod
    def log_error(
        error: Exception,
        context: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Log error with appropriate detail level.

        Args:
            error: Exception to log
            context: Additional context information
            logger: Logger instance (uses default if None)
        """
        if logger is None:
            logger = logging.getLogger(__name__)

        # Build log message
        log_parts = []
        if context:
            log_parts.append(f"Context: {context}")

        log_parts.append(f"Error: {type(error).__name__}: {str(error)}")

        log_message = " | ".join(log_parts)

        # Log with appropriate level
        if isinstance(error, SecurityError):
            logger.error(f"SECURITY ERROR: {log_message}")
        else:
            logger.error(log_message)

        # Include stack trace in debug mode
        if DEBUG_MODE:
            logger.debug("Stack trace:", exc_info=True)

    @staticmethod
    def handle_exception(
        error: Exception,
        context: Optional[str] = None,
        raise_error: bool = False,
        default_message: str = "An error occurred"
    ) -> str:
        """
        Comprehensive exception handling.

        Args:
            error: Exception to handle
            context: Additional context
            raise_error: Whether to re-raise the error
            default_message: Default user message

        Returns:
            User-friendly error message

        Raises:
            Exception: If raise_error is True
        """
        # Log the error
        SecureErrorHandler.log_error(error, context)

        # Get user message
        user_message = SecureErrorHandler.format_error_for_user(error, default_message)

        # Re-raise if requested
        if raise_error:
            if PRODUCTION_MODE and not DEBUG_MODE:
                # Raise generic error in production
                raise type(error)(default_message) from None
            else:
                raise

        return user_message


def secure_exception_handler(
    default_message: str = "An error occurred",
    context: Optional[str] = None,
    log_errors: bool = True
) -> Any:
    """
    Decorator for secure exception handling.

    Args:
        default_message: Default error message for users
        context: Context description
        log_errors: Whether to log errors

    Example:
        @secure_exception_handler(default_message="Failed to execute command")
        async def execute_command(self, cmd: str):
            # Function implementation
            pass
    """
    def decorator(func: Any) -> Any:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    SecureErrorHandler.log_error(e, context or func.__name__)

                # In production, raise generic error
                if PRODUCTION_MODE and not DEBUG_MODE:
                    raise type(e)(default_message) from None
                else:
                    # In development, show actual error
                    raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    SecureErrorHandler.log_error(e, context or func.__name__)

                # In production, raise generic error
                if PRODUCTION_MODE and not DEBUG_MODE:
                    raise type(e)(default_message) from None
                else:
                    # In development, show actual error
                    raise

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def suppress_stack_trace_in_production() -> None:
    """
    Suppress stack traces in production environment.

    Call this at application startup to configure global exception handling.
    """
    if PRODUCTION_MODE and not DEBUG_MODE:
        def custom_exception_hook(exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
            """Custom exception hook that hides stack traces in production"""
            # Log the full error internally
            logger = logging.getLogger(__name__)
            logger.error(
                f"Unhandled exception: {exc_type.__name__}: {exc_value}",
                exc_info=(exc_type, exc_value, exc_traceback)
            )

            # Show generic message to user
            print(f"Error: An unexpected error occurred", file=sys.stderr)

        # Install custom exception hook
        sys.excepthook = custom_exception_hook
