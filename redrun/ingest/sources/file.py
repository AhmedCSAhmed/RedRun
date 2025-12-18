from pathlib import Path
from typing import List

class FileSource:
    """
    FileSource is a class that reads a log file and returns a list of lines.
    
    path: str - the path to the log file
    """
    def __init__(self, path: Path):
        self.path = Path(path)

    def read(self) -> List[str]:
        with open(self.path, 'r') as file:
            return [line.rstrip("\n") for line in file]
    

    
    