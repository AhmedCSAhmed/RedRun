"""
StdinSource implementation for reading log data from standard input.

This module provides the StdinSource class which implements the Source
protocol for reading log data from stdin (standard input). This enables
piping log data from other commands or reading from interactive input.
"""

from typing import List
import sys


class StdinSource:
    """
    Source implementation for reading log data from standard input.
    
    StdinSource reads log data from stdin (standard input stream).
    It implements the Source protocol and can be used with Reader and
    Normalizer classes.
    
    This is useful for piping log data from other commands:
        cat build.log | redrun analyze
        tail -f app.log | redrun analyze
    
    The stdin stream is read line-by-line until EOF. Trailing newlines
    are stripped from each line. Note that stdin can only be read once
    - subsequent calls to read() will return an empty list if stdin has
    already been consumed.
    
    Attributes:
        stdin: The stdin stream (typically sys.stdin).
    
    Example:
        >>> source = StdinSource()
        >>> # Assuming stdin has data:
        >>> lines = source.read()  # Reads until EOF
    """
    
    def __init__(self):
        """
        Initialize StdinSource with sys.stdin.
        
        Creates a StdinSource that reads from sys.stdin. The stdin stream
        is captured at initialization time, so it can be read later.
        
        Note:
            StdinSource reads from the process's standard input stream.
            If stdin is a TTY (interactive terminal), read() will block
            until EOF is reached (Ctrl+D on Unix, Ctrl+Z on Windows).
            For non-interactive use, stdin should be piped or redirected.
        """
        self.stdin = sys.stdin

    def read(self) -> List[str]:
        """
        Read all lines from stdin until EOF.
        
        Reads all available data from stdin line-by-line until end-of-file
        (EOF) is reached. Each line has its trailing newline character
        stripped. The method blocks until EOF is encountered.
        
        Returns:
            List of log line strings. Each line has trailing newline
            characters removed. Empty list if stdin is empty or has
            already been read.
        
        Raises:
            IOError: If stdin cannot be read (should be rare).
            UnicodeDecodeError: If stdin contains invalid UTF-8 encoding.
        
        Note:
            - Stdin can only be read once. Subsequent calls will return
              an empty list if stdin has already been consumed.
            - If stdin is a TTY (interactive terminal), this method will
              block until EOF (Ctrl+D on Unix, Ctrl+Z+Enter on Windows).
            - For large inputs, this method loads all data into memory.
              Consider using streaming for very large logs.
        
        Example:
            >>> # From command line:
            >>> # echo -e "line1\\nline2" | python -c "from redrun.ingest.sources.stdin import StdinSource; print(StdinSource().read())"
            >>> # Output: ['line1', 'line2']
        """
        return [line.rstrip("\n") for line in self.stdin]