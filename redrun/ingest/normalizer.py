from typing import List, Dict
from .sources.source import Source
import re
import logging

logger = logging.getLogger(__name__)


class Normalizer:  
    """
    Normalizes raw log lines into structured format.
    
    Converts log lines from a Source into structured dictionaries with timestamp,
    level, and message fields. Tries multiple patterns to match common log formats.
    Lines matching any pattern are parsed; unmatched lines are marked as UNPARSED.
    
    Supports multiple log formats:
    - `[timestamp] level: message` - e.g., `[2024-01-15 10:30:45] ERROR: Database connection failed`
    - `[level] timestamp message` - e.g., `[ERROR] 2025-01-14T09:12:03.442Z Test failed`
    - `[level] message` - e.g., `[ERROR] Test failed`
    - `timestamp level message` - e.g., `2024-01-15 10:30:45 ERROR Database connection failed`
    - `level: message` - e.g., `ERROR: Database connection failed`
    """  
    
    # Multiple patterns to support various log formats (ordered from most specific to least)
    LOG_PATTERNS = [
        # Pattern 1: [level] timestamp message (timestamp is ISO format or similar) - check this FIRST
        re.compile(r'\[(?P<level>\w+)\] (?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[\.\d]*[Z]?) (?P<message>.*)'),
        # Pattern 2: [level] message (no timestamp) - check before pattern 3 to avoid false matches
        re.compile(r'\[(?P<level>\w+)\] (?P<message>.*)'),
        # Pattern 3: [timestamp] level: message (timestamp must contain numbers/colons, not just any text)
        re.compile(r'\[(?P<timestamp>\d{4}[-/]\d{2}[-/]\d{2}[T\s]?\d{2}:\d{2}:\d{2}[\.\d]*[Z\s]*)\] (?P<level>\w+): (?P<message>.*)'),
        # Pattern 4: timestamp level message (no brackets, timestamp first)
        re.compile(r'(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]?\d{2}:\d{2}:\d{2}[\.\d]*[Z]?) (?P<level>\w+) (?P<message>.*)'),
        # Pattern 5: level: message (simple format, no brackets)
        re.compile(r'^(?P<level>\w+): (?P<message>.*)'),
    ]
    
    def __init__(self, source: Source):
        """
        Initialize with a log source.
        
        Args:
            source: Source object that provides log lines via read() method.
                   Can be FileSource, StdinSource, or any Source implementation.
        
        Raises:
            ValueError: If source is not a Source instance.
        """
        if not isinstance(source, Source):
            raise ValueError("source must be an instance of Source")
        self.source = source
        logger.debug(f"Initialized Normalizer with source: {type(source).__name__}")
        
    
    def normalize(self) -> List[Dict[str, str]]:
        """
        Normalize log lines into structured format.
        
        Reads all lines from the source and converts them to structured dicts.
        Each dict contains: timestamp, level, message.
        
        Returns:
            List of dicts. Parsed lines have actual values; unparsed lines have
            timestamp="UNKNOWN", level="UNPARSED", message=original line.
        """
        logger.info("Starting normalization process")
        lines = self.source.read()
        logger.debug(f"Read {len(lines)} lines from source")
        return self._log_normalization_logic(lines)

    
    def _log_normalization_logic(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        Parse log lines using LOG_PATTERN regex.
        
        Matches each line against the pattern. Matching lines are parsed into
        structured dicts. Non-matching lines are marked as UNPARSED. Exceptions
        are caught and logged.
        
        Args:
            lines: Raw log line strings to normalize.
        
        Returns:
            List of normalized log dictionaries with timestamp, level, message.
        """
        logger.info(f"Normalizing {len(lines)} log lines")
        structured_logs = []
        
        parsed_count = 0
        unparsed_count = 0
        error_count = 0
        
        for line_num, line in enumerate(lines, start=1):
            try:
                # Try each pattern until one matches
                matched = False
                for pattern in self.LOG_PATTERNS:
                    match = pattern.match(line)
                    if match:
                        log_group = match.groupdict()
                        # Ensure all required fields exist
                        if 'timestamp' not in log_group:
                            log_group['timestamp'] = 'UNKNOWN'
                        if 'level' not in log_group:
                            log_group['level'] = 'UNPARSED'
                        if 'message' not in log_group:
                            log_group['message'] = line.strip()
                        
                        log_group["line_number"] = str(line_num)  # the line number of the log line
                        structured_logs.append(log_group)
                        parsed_count += 1
                        matched = True
                        logger.debug(f"Parsed log line (pattern matched): level={log_group.get('level')}, timestamp={log_group.get('timestamp')}")
                        break
                
                if not matched:
                    # No pattern matched
                    structured_logs.append({
                        "timestamp": "UNKNOWN",
                        "level": "UNPARSED",
                        "message": line.strip(),
                        "line_number": str(line_num)  
                    })
                    unparsed_count += 1
                    logger.warning(f"Could not parse log line (no pattern match): {line[:50]}...")
                     
            except Exception as e:
                logger.error(f"Error parsing log line: {e}", exc_info=True)
                structured_logs.append(
                    {
                        "timestamp": "ERROR PARSING LOG LINE",
                        "level": "ERROR",
                        "message": f"Error parsing log line: {e}",
                        "line_number": str(line_num)  
                    }
                )
                error_count += 1
        
        logger.info(f"Normalization complete: {parsed_count} parsed, {unparsed_count} unparsed, {error_count} errors")
        return structured_logs
        