from typing import List, Dict


class Extractor:
    """
    Extracts error events from normalized log entries.
    
    Filters normalized log entries to find error-level events based on log level.
    Takes structured log dictionaries from the normalizer and returns only those
    that match error criteria (e.g., ERROR, CRITICAL, FATAL levels).
    """
    # def __init__(self, Errors = ["ERROR", "FATAL", "CRITICAL"]):
        