"""
FileSource implementation for reading log files from the filesystem.

This module provides the FileSource class which implements the Source
protocol for reading log data from files on the local filesystem.
"""

from pathlib import Path
from typing import List


class FileSource:
    """
    Source implementation for reading log files from the filesystem.
    
    FileSource reads log data from a file on the local filesystem.
    It implements the Source protocol and can be used with Reader and
    Normalizer classes.
    
    The file is opened in text mode and read line-by-line. Trailing
    newlines are stripped from each line. The file is automatically
    closed after reading.
    
    Attributes:
        path: Path to the log file (pathlib.Path object).
    
    Example:
        >>> source = FileSource("build.log")
        >>> lines = source.read()
        >>> # Or with Path:
        >>> source = FileSource(Path("/var/log/app.log"))
        >>> lines = source.read()
    """
    
    def __init__(self, path: Path | str):
        """
        Initialize FileSource with a file path.
        
        Args:
            path: Path to the log file. Can be a string or pathlib.Path.
                 If a string is provided, it will be converted to a Path.
                 Relative paths are resolved relative to the current
                 working directory.
        
        Raises:
            TypeError: If path is not a string or Path object.
        
        Note:
            The file is not opened during initialization. It is opened
            only when read() is called.
        """
        self.path = Path(path)

    def read(self) -> List[str]:
        """
        Read all lines from the file.
        
        Opens the file in text mode, reads all lines, strips trailing
        newlines, and returns them as a list. The file is automatically
        closed after reading completes (even if an error occurs).
        
        Returns:
            List of log line strings. Each line has trailing newline
            characters removed. Empty list if file is empty.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read due to insufficient
                            permissions.
            IsADirectoryError: If the path points to a directory, not a file.
            UnicodeDecodeError: If the file contains invalid UTF-8 encoding.
            IOError: For other I/O errors (e.g., disk full, device error).
        
        Example:
            >>> source = FileSource("app.log")
            >>> lines = source.read()
            >>> print(f"Read {len(lines)} lines")
        """
        with open(self.path, 'r') as file:
            return [line.rstrip("\n") for line in file]
    