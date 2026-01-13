"""
Error extraction module.

This module provides the Extractor class which filters normalized log
entries to identify error-level events and stack traces. It uses compiled
regex patterns for efficient detection of Python and Java stack traces,
as well as filtering by log level (ERROR, FATAL, CRITICAL).
"""

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
    PYTHON_TRACEBACK = re.compile(r'Traceback\s*\(most recent call last\)', re.IGNORECASE)
    PYTHON_FILE_REF = re.compile(r'File\s+"[^"]+"', re.IGNORECASE)
    PYTHON_MEMORY_ADDR = re.compile(r'at\s+0x[0-9a-f]+', re.IGNORECASE)
    
    JAVA_EXCEPTION = re.compile(r'java\.(lang|sql|io|util|net)\.[\w.]+(Exception|Error):', re.IGNORECASE)
    JAVA_STACK_LINE = re.compile(r'\s+at\s+[\w.$]+\.[\w$]+\s*\([^)]+\.(java|kt|scala|groovy):\d+\)', re.IGNORECASE)
    JAVA_CAUSED_BY = re.compile(r'Caused by:', re.IGNORECASE)
    
    EXCEPTION_TYPE = re.compile(r'\w+(Exception|Error):', re.IGNORECASE)
    AT_WITH_PATH = re.compile(r'\s+at\s+.*[/\\].*\(', re.IGNORECASE)
    
    def __init__(self, errors: set[str] = None):
        """
        Initialize with error levels to extract.
        
        Args:
            errors: Set of log levels to extract (default: ERROR, FATAL, CRITICAL)
        """
        
        self.errors = {e.upper() for e in (errors or {"ERROR", "FATAL", "CRITICAL"})}
        self.filtered_noise_count = 0
        self.total_lines_processed = 0
        logger.debug(f"Initialized Extractor with error levels: {self.errors}")

    
    def extract(self, log_entries: List[Dict[str, str]]) -> Iterator[Dict[str, str]]:
        """
        Extract error events from normalized log entries.
        
        Extracts entries that match error levels (ERROR, FATAL, CRITICAL) or
        contain stack traces, which are important for debugging CI failures.
        Binds UNPARSED exception lines to the nearest preceding ERROR within +-3 lines.
        Tracks filtered noise (lines that were not extracted).
        
        Args:
            log_entries: List of normalized log dictionaries.
        
        Yields:
            Log entries that match error criteria (level in self.errors).
            UNPARSED exceptions are merged into preceding ERROR entries when found within ±3 lines.
        """
        self.filtered_noise_count = 0
        self.total_lines_processed = len(log_entries)
        
        # First pass: identify which UNPARSED exceptions should be bound to which ERROR entries
        # Map ERROR entry indices to list of UNPARSED exception messages to merge
        error_bindings = {}  # {error_idx: [unparsed_messages]}
        
        for idx, log_entry in enumerate(log_entries):
            try:
                level = log_entry.get('level', '').upper()
                if level == 'UNPARSED':
                    message = log_entry.get('message', '')
                    if self._has_exception_type(message) and not self._is_traceback_header(message):
                        # Look backwards for nearest ERROR within ±3 lines
                        bound_idx = None
                        for back_idx in range(max(0, idx - 3), idx):
                            prev_entry = log_entries[back_idx]
                            prev_level = prev_entry.get('level', '').upper()
                            if prev_level in self.errors:
                                # Check line number distance if available
                                try:
                                    current_line = int(log_entry.get('line_number', '0'))
                                    prev_line = int(prev_entry.get('line_number', '0'))
                                    if abs(current_line - prev_line) <= 3:
                                        bound_idx = back_idx
                                        break
                                except (ValueError, TypeError):
                                    # Line numbers unavailable, use index distance
                                    bound_idx = back_idx
                                    break
                        
                        if bound_idx is not None:
                            # Bind this UNPARSED exception to the ERROR entry
                            if bound_idx not in error_bindings:
                                error_bindings[bound_idx] = []
                            error_bindings[bound_idx].append(message)
                            logger.debug(f"Binding UNPARSED exception to ERROR at index {bound_idx}")
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error processing log entry for binding: {e}, skipping entry")
                continue
        
        # Second pass: yield entries with bindings applied
        for idx, log_entry in enumerate(log_entries):
            try:
                level = log_entry.get('level', '').upper()
                message = log_entry.get('message', '')
                
                if level in self.errors:
                    # Merge any bound UNPARSED exceptions into this ERROR entry
                    if idx in error_bindings:
                        unparsed_messages = error_bindings[idx]
                        merged_message = message + '\n' + '\n'.join(unparsed_messages)
                        # Create a copy to avoid modifying the original
                        error_entry = log_entry.copy()
                        error_entry['message'] = merged_message
                        yield error_entry
                    else:
                        yield log_entry
                elif level == 'UNPARSED':
                    # Only yield UNPARSED entries that weren't bound to an ERROR
                    if self._has_exception_type(message) and not self._is_traceback_header(message):
                        # Check if this UNPARSED was bound to an ERROR
                        was_bound = False
                        for bound_idx, messages in error_bindings.items():
                            if message in messages:
                                was_bound = True
                                break
                        if not was_bound:
                            yield log_entry
                    else:
                        self.filtered_noise_count += 1
                        continue
                elif self._is_stack_trace(message):
                    yield log_entry
                else:
                    self.filtered_noise_count += 1
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
        
        if (self.PYTHON_TRACEBACK.search(message) or
            self.PYTHON_FILE_REF.search(message) or
            self.PYTHON_MEMORY_ADDR.search(message)):
            return True
        
        if (self.JAVA_EXCEPTION.search(message) or
            self.JAVA_STACK_LINE.search(message) or
            self.JAVA_CAUSED_BY.search(message)):
            return True
        
        if (self.EXCEPTION_TYPE.search(message) or
            self.AT_WITH_PATH.search(message)):
            return True
        
        return False
    
    def _is_traceback_header(self, message: str) -> bool:
        """
        Check if the message is just a traceback header/continuation line.
        
        These are lines like "Traceback (most recent call last):" or "File ..."
        that don't contain the actual exception - they're just context.
        
        Args:
            message: The message to check.
        
        Returns:
            True if this is just a traceback header line, False otherwise.
        """
        if not message:
            return False
        
        if self.PYTHON_TRACEBACK.search(message) and not self.EXCEPTION_TYPE.search(message):
            return True
        
        if self.PYTHON_FILE_REF.search(message) and not self.EXCEPTION_TYPE.search(message):
            return True
        
        if self.PYTHON_MEMORY_ADDR.search(message) and not self.EXCEPTION_TYPE.search(message):
            return True
        
        return False
    
    def _has_exception_type(self, message: str) -> bool:
        """
        Check if the message contains an actual exception type.
        
        Args:
            message: The message to check.
        
        Returns:
            True if the message contains an exception type, False otherwise.
        """
        if not message:
            return False
        
        return bool(self.EXCEPTION_TYPE.search(message) or 
                   self.JAVA_EXCEPTION.search(message))
                
        
        