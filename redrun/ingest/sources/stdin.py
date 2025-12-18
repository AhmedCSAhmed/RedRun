from typing import List
import sys

class StdinSource:
    """
    StdinSource is a class that reads a log file from stdin.
    """
    
    def __init__(self):
        self.stdin = sys.stdin

    def read(self) -> List[str]:
        return [line.rstrip("\n") for line in self.stdin]