"""
Reader module for reading log data from various sources.

This module provides the Reader class which acts as a facade for reading
log data from different sources (files, stdin) using the Source protocol.
"""

from typing import List
from .sources.source import Source
from .sources.file import FileSource
from .sources.stdin import StdinSource
from pathlib import Path


class Reader:
    """
    Reader for log data from various sources.
    
    The Reader class provides a unified interface for reading log lines from
    different sources (files, stdin) using the Source protocol pattern.
    It acts as a factory and facade, providing convenient class methods
    for creating readers from common sources.
    
    Attributes:
        source: The Source implementation used to read log data.
    
    Example:
        >>> reader = Reader.from_file("build.log")
        >>> lines = reader.read()
        >>> # Or from stdin:
        >>> reader = Reader.from_stdin()
        >>> lines = reader.read()
    """
    
    def __init__(self, source: Source):
        """
        Initialize a Reader with a Source implementation.
        
        Args:
            source: A Source instance that implements the read() method.
                   Can be FileSource, StdinSource, or any custom Source.
        
        Raises:
            TypeError: If source does not implement the Source protocol.
        """
        self.source = source
    
    
    def read(self) -> List[str]:
        """
        Read all lines from the source.
        
        Delegates to the underlying Source's read() method to retrieve
        all log lines. Each line is returned as a string in the list.
        
        Returns:
            List of log line strings. Lines are stripped of trailing newlines.
        
        Raises:
            IOError: If the source cannot be read (e.g., file not found).
            ValueError: If the source is invalid or corrupted.
        """
        return self.source.read()
            
    
    @classmethod
    def from_file(cls, path: Path | str) -> 'Reader':
        """
        Create a Reader from a file path.
        
        Factory method that creates a FileSource and wraps it in a Reader.
        The path can be a string or Path object, and will be converted to
        a Path internally.
        
        Args:
            path: Path to the log file. Can be a string or pathlib.Path.
                 Relative paths are resolved relative to the current working directory.
        
        Returns:
            A Reader instance configured to read from the specified file.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read due to permissions.
        
        Example:
            >>> reader = Reader.from_file("build.log")
            >>> reader = Reader.from_file(Path("/var/log/app.log"))
        """
        return cls(FileSource(path))
    
    @classmethod
    def from_stdin(cls) -> "Reader":
        """
        Create a Reader from standard input.
        
        Factory method that creates a StdinSource and wraps it in a Reader.
        This allows reading log data piped from other commands or entered
        interactively (though interactive input is not recommended for large logs).
        
        Returns:
            A Reader instance configured to read from stdin.
        
        Example:
            >>> # From command line:
            >>> # cat build.log | redrun analyze
            >>> # Or in Python:
            >>> reader = Reader.from_stdin()
            >>> lines = reader.read()  # Reads until EOF
        """
        return cls(StdinSource())
