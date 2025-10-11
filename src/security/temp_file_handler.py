"""
Secure Temporary File Handling

Provides utilities for creating and managing temporary files securely.
"""

import tempfile
import os
from pathlib import Path
from typing import Optional, Union, BinaryIO, TextIO
from contextlib import contextmanager


class SecureTempFile:
    """Secure temporary file handler with automatic cleanup"""

    @staticmethod
    @contextmanager
    def create_temp_file(
        mode: str = 'w+b',
        suffix: Optional[str] = None,
        prefix: Optional[str] = 'ai-shell-',
        dir: Optional[Union[str, Path]] = None,
        delete: bool = True
    ):
        """
        Create a secure temporary file with proper permissions.

        Args:
            mode: File mode ('w+b' for binary, 'w+' for text)
            suffix: File suffix (e.g., '.txt')
            prefix: File prefix
            dir: Directory for temp file
            delete: Delete file on close

        Yields:
            File object

        Example:
            with SecureTempFile.create_temp_file(suffix='.txt') as f:
                f.write(b'secure data')
                f.flush()
                # File is automatically deleted after block
        """
        # Create temporary file with secure permissions
        fd = None
        temp_path = None

        try:
            # Create with secure permissions (0o600 - owner read/write only)
            fd = tempfile.mkstemp(
                suffix=suffix,
                prefix=prefix,
                dir=dir,
                text=False if 'b' in mode else True
            )
            temp_path = fd[1]
            os.close(fd[0])  # Close the file descriptor

            # Set restrictive permissions
            os.chmod(temp_path, 0o600)

            # Open with requested mode
            file_obj = open(temp_path, mode)

            try:
                yield file_obj
            finally:
                file_obj.close()

                # Delete file if requested
                if delete and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except OSError:
                        pass  # Best effort deletion

        except Exception:
            # Cleanup on error
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise

    @staticmethod
    @contextmanager
    def create_temp_directory(
        suffix: Optional[str] = None,
        prefix: Optional[str] = 'ai-shell-',
        dir: Optional[Union[str, Path]] = None
    ):
        """
        Create a secure temporary directory with proper permissions.

        Args:
            suffix: Directory suffix
            prefix: Directory prefix
            dir: Parent directory

        Yields:
            Path to temporary directory

        Example:
            with SecureTempFile.create_temp_directory() as temp_dir:
                config_file = temp_dir / 'config.yaml'
                config_file.write_text('data')
                # Directory is automatically deleted after block
        """
        temp_dir = None

        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(
                suffix=suffix,
                prefix=prefix,
                dir=dir
            )

            # Set restrictive permissions (0o700 - owner only)
            os.chmod(temp_dir, 0o700)

            yield Path(temp_dir)

        finally:
            # Cleanup directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except OSError:
                    pass  # Best effort deletion

    @staticmethod
    def create_named_temp_file(
        mode: str = 'w+b',
        suffix: Optional[str] = None,
        prefix: Optional[str] = 'ai-shell-',
        dir: Optional[Union[str, Path]] = None,
        delete: bool = True
    ) -> Union[BinaryIO, TextIO]:
        """
        Create a named temporary file (can be opened multiple times).

        Args:
            mode: File mode
            suffix: File suffix
            prefix: File prefix
            dir: Directory for temp file
            delete: Delete file on close

        Returns:
            NamedTemporaryFile object

        Example:
            temp_file = SecureTempFile.create_named_temp_file(suffix='.txt')
            temp_file.write(b'data')
            temp_file.flush()
            # Use temp_file.name to get path
            temp_file.close()  # Auto-deleted
        """
        # NamedTemporaryFile with secure defaults
        temp_file = tempfile.NamedTemporaryFile(
            mode=mode,
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            delete=delete
        )

        # Set restrictive permissions
        os.chmod(temp_file.name, 0o600)

        return temp_file

    @staticmethod
    def secure_write(file_path: Union[str, Path], content: Union[str, bytes]) -> None:
        """
        Write content to file with secure permissions.

        Args:
            file_path: Path to file
            content: Content to write (str or bytes)

        Example:
            SecureTempFile.secure_write('/path/to/file.txt', 'secret data')
        """
        path = Path(file_path)

        # Determine write mode
        mode = 'wb' if isinstance(content, bytes) else 'w'

        # Write file
        with open(path, mode) as f:
            f.write(content)

        # Set secure permissions
        path.chmod(0o600)

    @staticmethod
    def secure_directory(dir_path: Union[str, Path]) -> Path:
        """
        Create directory with secure permissions or fix existing permissions.

        Args:
            dir_path: Directory path

        Returns:
            Path object

        Example:
            secure_dir = SecureTempFile.secure_directory('~/.ai-shell')
        """
        path = Path(dir_path).expanduser()
        path.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions (0o700 - owner only)
        path.chmod(0o700)

        return path
