"""
Source protocol for reading log data.

This module defines the Source protocol (interface) that all log data
sources must implement. It uses Python's Protocol class for structural
subtyping, allowing any class with a read() method to be used as a Source.
"""

from typing import List, Protocol, runtime_checkable


@runtime_checkable
class Source(Protocol):
    """
    Protocol (interface) for log data sources.
    
    The Source protocol defines the contract that all log data sources
    must follow. Any class implementing a read() method that returns
    a list of strings can be used as a Source.
    
    This protocol enables polymorphism - the Reader and Normalizer classes
    can work with any Source implementation (FileSource, StdinSource, etc.)
    without knowing the specific implementation details.
    
    The protocol is runtime-checkable, meaning isinstance() checks will
    work for classes that implement the protocol, even if they don't
    explicitly inherit from Source.
    
    Example:
        >>> class CustomSource:
        ...     def read(self) -> List[str]:
        ...         return ["line1", "line2"]
        >>> 
        >>> source = CustomSource()
        >>> isinstance(source, Source)  # True
        >>> reader = Reader(source)  # Works!
    """
    
    def read(self) -> List[str]:
        """
        Read all lines from the source.
        
        This method should read all available data from the source and
        return it as a list of strings. Each string represents one line
        of log data. Trailing newlines should be stripped.
        
        Returns:
            List of log line strings. Empty list if source is empty.
            Lines should not include trailing newline characters.
        
        Raises:
            IOError: If the source cannot be read (e.g., file not found,
                    permission denied, network error).
            ValueError: If the source data is invalid or corrupted.
        
        Note:
            This method should be idempotent - calling it multiple times
            should return the same data (unless the source is stateful
            like stdin, which reads until EOF).
        """
        ...