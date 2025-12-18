from typing import List
from .sources.source import Source
from .sources.file import FileSource
from .sources.stdin import StdinSource
from pathlib import Path


class Reader:
    def __init__(self, source: Source):
        """
        Reader is a class that reads a log file and returns a list of lines.
        
        source: str - the path to the log file
        """
        self.source = source
    
    
    def read(self) -> List[str]:
        return self.source.read()
            
    
    @classmethod
    def from_file(cls, path: Path | str) -> 'Reader':
        return cls(FileSource(path))
    
    @classmethod
    def from_stdin(cls) -> "Reader":
        return cls(StdinSource())
