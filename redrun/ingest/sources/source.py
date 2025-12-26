from typing import List, Protocol, runtime_checkable


@runtime_checkable
class Source(Protocol):
    """"
    Source is a protocol that defines the read method.
    Implementing classes must define the read method.
    
    """
    def read(self) -> List[str]:
        """
        Read the source and return a list of lines.
        """
        ...