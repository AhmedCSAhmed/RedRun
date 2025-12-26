from typing import List, Dict, Iterator


class Extractor:
    """
    Extracts error events from normalized log entries.
    
    Filters normalized log entries to find error-level events based on log level.
    Takes structured log dictionaries from the normalizer and returns only those
    that match error criteria (e.g., ERROR, CRITICAL, FATAL levels).
    """
    
    def __init__(self, errors: set[str] = None):
        """
        Initialize with error levels to extract.
        
        Args:
            errors: Set of log levels to extract (default: ERROR, FATAL, CRITICAL)
        """
        
        self.errors = {e.upper() for e in (errors or {"ERROR", "FATAL", "CRITICAL"})} # convert to uppercase for case insensitivity

    
    def extract(self, log_entries: List[Dict[str, str]]) -> Iterator[Dict[str, str]]:
        """
        Extract error events from normalized log entries.
        
        Extracts entries that match error levels (ERROR, FATAL, CRITICAL) or
        contain stack traces, which are important for debugging CI failures.
        
        Args:
            log_entries: List of normalized log dictionaries.
        
        Yields:
            Log entries that match error criteria (level in self.errors).
        """
        for log_entry in log_entries:
            try:
                level = log_entry.get('level', '').upper()  # Convert to uppercase for case-insensitive comparison
                message = log_entry.get('message', '')
                
                if level in self.errors or self._is_stack_trace(message):
                    yield log_entry
            except (KeyError, ValueError, TypeError):
                # Skip entries with missing keys or invalid format
                continue 
    

    
    def _is_stack_trace(self, message: str) -> bool:
        """
        Check if the message contains a stack trace.
        
        Detects common stack trace patterns like "Traceback", "File", "at ",
        and exception type indicators.
        
        Args:
            message: The message to check.
        
        Returns:
            True if the message contains stack trace patterns, False otherwise.
        """
        if not message:
            return False
        
        stack_trace_indicators = [
            "Traceback (most recent call last)",
            "Traceback",
            "File \"",
            "at 0x",  # Memory addresses in stack traces
            "  File \"",  # Indented file references
        ]
        
        for indicator in stack_trace_indicators:
            if indicator in message:
                return True
        
        # Check for "at " followed by file path pattern (more specific than just "at")
        if " at " in message and ("/" in message or "\\" in message):
            return True
        
        return False
                
        
        