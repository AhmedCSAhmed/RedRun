from typing import List, Dict, Iterator
import re
import logging

logger = logging.getLogger(__name__)


class Extractor:
    """
    Extracts error events from normalized log entries.
    
    Filters normalized log entries to find error-level events based on log level.
    Takes structured log dictionaries from the normalizer and returns only those
    that match error criteria (e.g., ERROR, CRITICAL, FATAL levels) or
    contain stack traces.
    """
    # Everything is compiled once at class initialization time to avoid re-compiling on every log entry
    
    # Compiled regex patterns for stack trace detection
    # Python stack trace patterns
    PYTHON_TRACEBACK = re.compile(r'Traceback\s*\(most recent call last\)', re.IGNORECASE)
    PYTHON_FILE_REF = re.compile(r'File\s+"[^"]+"', re.IGNORECASE)
    PYTHON_MEMORY_ADDR = re.compile(r'at\s+0x[0-9a-f]+', re.IGNORECASE)
    
    # Java stack trace patterns
    JAVA_EXCEPTION = re.compile(r'java\.(lang|sql|io|util|net)\.[\w.]+(Exception|Error):', re.IGNORECASE)
    JAVA_STACK_LINE = re.compile(r'\s+at\s+[\w.$]+\.[\w$]+\s*\([^)]+\.(java|kt|scala|groovy):\d+\)', re.IGNORECASE)
    JAVA_CAUSED_BY = re.compile(r'Caused by:', re.IGNORECASE)
    
    # Generic patterns
    EXCEPTION_TYPE = re.compile(r'\w+(Exception|Error):', re.IGNORECASE)
    AT_WITH_PATH = re.compile(r'\s+at\s+.*[/\\].*\(', re.IGNORECASE)
    
    def __init__(self, errors: set[str] = None):
        """
        Initialize with error levels to extract.
        
        Args:
            errors: Set of log levels to extract (default: ERROR, FATAL, CRITICAL)
        """
        
        self.errors = {e.upper() for e in (errors or {"ERROR", "FATAL", "CRITICAL"})} # convert to uppercase for case insensitivity
        self.filtered_noise_count = 0  # Track lines filtered out (non-errors)
        self.total_lines_processed = 0  # Track total lines processed
        logger.debug(f"Initialized Extractor with error levels: {self.errors}")

    
    def extract(self, log_entries: List[Dict[str, str]]) -> Iterator[Dict[str, str]]:
        """
        Extract error events from normalized log entries.
        
        Extracts entries that match error levels (ERROR, FATAL, CRITICAL) or
        contain stack traces, which are important for debugging CI failures.
        Tracks filtered noise (lines that were not extracted).
        
        Args:
            log_entries: List of normalized log dictionaries.
        
        Yields:
            Log entries that match error criteria (level in self.errors).
        """
        # Reset counters for this extraction
        self.filtered_noise_count = 0
        self.total_lines_processed = len(log_entries)
        
        for log_entry in log_entries:
            try:
                level = log_entry.get('level', '').upper()  # Convert to uppercase for case-insensitive comparison
                message = log_entry.get('message', '')
                
                if level in self.errors or self._is_stack_trace(message):
                    yield log_entry
                else:
                    self.filtered_noise_count += 1 # We filtered out this line as ("noise")
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error processing log entry in Extractor: {e}, skipping entry: {log_entry}")
                self.filtered_noise_count += 1
                continue
        
        logger.info(f"Extracted {self.total_lines_processed - self.filtered_noise_count} error events from {self.total_lines_processed} log entries")
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get extraction statistics.
        
        Returns:
            Dictionary with stats: total_lines, extracted_count, filtered_noise_count
        """
        extracted_count = self.total_lines_processed - self.filtered_noise_count
        return {
            "total_lines": self.total_lines_processed,
            "extracted_count": extracted_count,
            "filtered_noise_count": self.filtered_noise_count
        } 
    

    
    def _is_stack_trace(self, message: str) -> bool:
        """
        Check if the message contains a stack trace.
        
        Uses compiled regex patterns to detect stack traces from Python, Java,
        and other languages. Patterns are case-insensitive for better matching.
        
        Args:
            message: The message to check.
        
        Returns:
            True if the message contains stack trace patterns, False otherwise.
        """
        if not message:
            return False
        
        # Checking Python patterns for stack traces
        if (self.PYTHON_TRACEBACK.search(message) or
            self.PYTHON_FILE_REF.search(message) or
            self.PYTHON_MEMORY_ADDR.search(message)):
            return True
        
        # Checking Java patterns for stack traces
        if (self.JAVA_EXCEPTION.search(message) or
            self.JAVA_STACK_LINE.search(message) or
            self.JAVA_CAUSED_BY.search(message)):
            return True
        
        # Checking generic patterns (exception types, "at" with file paths) for stack traces
        if (self.EXCEPTION_TYPE.search(message) or
            self.AT_WITH_PATH.search(message)):
            return True
        
        return False
                
        
        