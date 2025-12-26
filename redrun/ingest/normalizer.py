from typing import List, Dict
from .sources.source import Source
import re
import logging

logger = logging.getLogger(__name__)


class Normalizer:  
    """
    Normalizes raw log lines into structured format.
    
    Converts log lines from a Source into structured dictionaries with timestamp,
    level, and message fields. Lines matching the pattern are parsed; unmatched
    lines are marked as UNPARSED.
    
    Expected format: `[timestamp] level: message`
    Example: `[2024-01-15 10:30:45] ERROR: Database connection failed`
    """  
    
    LOG_PATTERN = re.compile(
            r'\[(?P<timestamp>[^\]]+)\] '
            r'(?P<level>\w+): '
            r'(?P<message>.*)'
            )
    
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
        
        for line in lines:
            try:
                match = self.LOG_PATTERN.match(line)
                if match:
                    log_group = match.groupdict()
                    structured_logs.append(log_group)
                    parsed_count += 1
                    logger.debug(f"Parsed log line: level={log_group.get('level')}, timestamp={log_group.get('timestamp')}")
                else:
                    structured_logs.append({
                        "timestamp": "UNKNOWN",
                        "level": "UNPARSED",
                        "message": line.strip()
                    })
                    unparsed_count += 1
                    logger.warning(f"Could not parse log line (no pattern match): {line[:50]}...")
                     
            except Exception as e:
                logger.error(f"Error parsing log line: {e}", exc_info=True)
                structured_logs.append(
                    {
                        "timestamp": "ERROR PARSING LOG LINE",
                        "level": "ERROR",
                        "message": f"Error parsing log line: {e}"
                    }
                )
                error_count += 1
        
        logger.info(f"Normalization complete: {parsed_count} parsed, {unparsed_count} unparsed, {error_count} errors")
        return structured_logs
        