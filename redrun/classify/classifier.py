from typing import Dict, List, Tuple, Optional
import re
import logging
from collections import defaultdict
from .categories import (
    TEST_FAILURE, DEPENDENCY_FAILURE, INFRA_TIMEOUT, BUILD_ERROR,
    LINT_ERROR, AUTH_ERROR, NETWORK_ERROR, CONFIG_ERROR,
    DB_ERROR, PERMISSION_ERROR, RESOURCE_ERROR, OTHER
)

logger = logging.getLogger(__name__)


class Classifier:
    """
    Classifies error entries into categories using pattern matching.
    
    Takes extracted error entries and categorizes them based on message
    patterns. Uses deterministic rule-based matching for explainability.
    """
    
    def __init__(self):
        # Pattern performance tracking
        self.pattern_stats = defaultdict(int)  # Tracking how often each pattern matches
        self.category_stats = defaultdict(int)  # Tracking category distribution
        # Compiled regex patterns for each category (ordered by specificity)
        # Format: (category, pattern, description)
        # Using word boundaries (\b) for more precise matching and handling variations
        self.patterns = [
            # Test failures - more robust patterns
            (TEST_FAILURE, re.compile(r'\btest\s+(failed|failure|failures|failing)\b', re.IGNORECASE), "test failed pattern"),
            (TEST_FAILURE, re.compile(r'\bassertion\s*(error|failed|failure)\b', re.IGNORECASE), "assertion error pattern"),
            (TEST_FAILURE, re.compile(r'\btest\s+.*\s+(failed|failure|error)\b', re.IGNORECASE), "test error pattern"),
            (TEST_FAILURE, re.compile(r'\.test\.|Test.*\.(java|kt|scala)|.*Test\.(py|js|ts)', re.IGNORECASE), "test file pattern"),
            (TEST_FAILURE, re.compile(r'\btest\s+suite.*(failed|error|exception)\b', re.IGNORECASE), "test suite failure pattern"),
            (TEST_FAILURE, re.compile(r'\b(test|tests)\s+(are|is)\s+(failing|broken)\b', re.IGNORECASE), "tests failing pattern"),
            
            # Database errors (check before generic SQL exceptions) - more patterns
            (DB_ERROR, re.compile(r'\b(sql|database|db)\s+.*\s+(exception|error|failure)\b', re.IGNORECASE), "SQL/database error pattern"),
            (DB_ERROR, re.compile(r'\b(connection\s+pool|hikari.*pool|jdbc|datasource)\b', re.IGNORECASE), "connection pool pattern"),
            (DB_ERROR, re.compile(r'\bconnection\s+(is\s+)?not\s+available\b', re.IGNORECASE), "connection not available pattern"),
            (DB_ERROR, re.compile(r'\b(query|transaction|sql)\s+timeout\b', re.IGNORECASE), "query timeout pattern"),
            (DB_ERROR, re.compile(r'\b(deadlock|lock\s+timeout|connection\s+refused)\b', re.IGNORECASE), "deadlock pattern"),
            (DB_ERROR, re.compile(r'\bsql(transient|timeout|connection)?exception\b', re.IGNORECASE), "SQL exception pattern"),
            (DB_ERROR, re.compile(r'\bdatabase\s+connection\s+(failed|error|lost)\b', re.IGNORECASE), "database connection failure pattern"),
            
            # Network errors - expanded patterns
            (NETWORK_ERROR, re.compile(r'\bconnection\s+(reset|refused|closed|dropped|failed)\b', re.IGNORECASE), "connection reset/refused pattern"),
            (NETWORK_ERROR, re.compile(r'\b(network|socket|http|tcp|udp)\s+.*\s+(error|exception|failure)\b', re.IGNORECASE), "network protocol error pattern"),
            (NETWORK_ERROR, re.compile(r'\bconnection\s+timeout|network\s+unreachable\b', re.IGNORECASE), "network timeout pattern"),
            (NETWORK_ERROR, re.compile(r'\b(dns|hostname|resolve).*\s+(error|failed|unreachable)\b', re.IGNORECASE), "DNS resolution error pattern"),
            (NETWORK_ERROR, re.compile(r'\b(connection|network|socket)\s+.*\s+(error|exception)\b', re.IGNORECASE), "network error pattern"),
            (NETWORK_ERROR, re.compile(r'\b(peer|server|client)\s+.*\s+(reset|refused|closed)\b', re.IGNORECASE), "peer connection error pattern"),
            
            # Configuration errors - more variations
            (CONFIG_ERROR, re.compile(r'\brequired\s+.*\s+(configuration|config|value|setting|parameter).*\s+missing\b', re.IGNORECASE), "required config missing pattern"),
            (CONFIG_ERROR, re.compile(r'\b(config|configuration|setting).*\s+(error|missing|invalid|not\s+found)\b', re.IGNORECASE), "config error pattern"),
            (CONFIG_ERROR, re.compile(r'\benvironment\s+variable.*missing|env\s+var.*not\s+set\b', re.IGNORECASE), "environment variable missing pattern"),
            (CONFIG_ERROR, re.compile(r'\billegalstateexception.*required|required.*value.*missing\b', re.IGNORECASE), "required value missing pattern"),
            (CONFIG_ERROR, re.compile(r'\b(missing|invalid|incorrect).*\s+(config|configuration|setting)\b', re.IGNORECASE), "missing/invalid config pattern"),
            
            # Infrastructure timeouts - broader coverage
            (INFRA_TIMEOUT, re.compile(r'\b(timeout|timed\s+out|time\s+out)\b', re.IGNORECASE), "timeout pattern"),
            (INFRA_TIMEOUT, re.compile(r'\b(request|operation|connection|health\s+check|container).*\s+timeout\b', re.IGNORECASE), "operation timeout pattern"),
            (INFRA_TIMEOUT, re.compile(r'\bexceeded.*time.*limit|time.*limit.*exceeded\b', re.IGNORECASE), "time limit exceeded pattern"),
            
            # Build errors - more comprehensive
            (BUILD_ERROR, re.compile(r'\bbuild\s+(failed|failure|error|broken)\b', re.IGNORECASE), "build failed pattern"),
            (BUILD_ERROR, re.compile(r'\b(compilation|compile|building).*\s+(error|failed|failure)\b', re.IGNORECASE), "compilation error pattern"),
            (BUILD_ERROR, re.compile(r'\bsyntax\s+error|parse\s+error|compilation\s+error\b', re.IGNORECASE), "syntax error pattern"),
            (BUILD_ERROR, re.compile(r'\bcannot\s+resolve|could\s+not\s+resolve|unresolved\b', re.IGNORECASE), "unresolved reference pattern"),
            (BUILD_ERROR, re.compile(r'\bpackage.*not\s+found|class.*not\s+found|module.*not\s+found\b', re.IGNORECASE), "package/class not found pattern"),
            (BUILD_ERROR, re.compile(r'\bbuild\s+.*\s+(failed|error|aborted|stopped)\b', re.IGNORECASE), "build failure pattern"),
            
            # Dependency errors - expanded
            (DEPENDENCY_FAILURE, re.compile(r'\bdependency.*(error|failed|failure|missing|not\s+found)\b', re.IGNORECASE), "dependency error pattern"),
            (DEPENDENCY_FAILURE, re.compile(r'\bpackage.*not\s+found|module.*not\s+found|library.*missing\b', re.IGNORECASE), "package/module not found pattern"),
            (DEPENDENCY_FAILURE, re.compile(r'\b(maven|gradle|npm|pip|yarn).*\s+(error|failed|failure)\b', re.IGNORECASE), "package manager error pattern"),
            (DEPENDENCY_FAILURE, re.compile(r'\bcannot\s+resolve.*dependency|failed\s+to\s+resolve\b', re.IGNORECASE), "dependency resolution failure pattern"),
            (DEPENDENCY_FAILURE, re.compile(r'\bversion\s+conflict|dependency\s+conflict|conflicting\s+dependencies\b', re.IGNORECASE), "version conflict pattern"),
            
            # Authentication errors
            (AUTH_ERROR, re.compile(r'\bauthentication\s+(failed|error|failure|denied)\b', re.IGNORECASE), "authentication failed pattern"),
            (AUTH_ERROR, re.compile(r'\bunauthorized|auth\s+(error|failed|failure)\b', re.IGNORECASE), "unauthorized pattern"),
            (AUTH_ERROR, re.compile(r'\binvalid\s+(credentials|token|password|api\s+key)\b', re.IGNORECASE), "invalid credentials pattern"),
            (AUTH_ERROR, re.compile(r'\btoken\s+(expired|invalid|missing)|session\s+expired\b', re.IGNORECASE), "token expired pattern"),
            
            # Permission errors - more specific
            (PERMISSION_ERROR, re.compile(r'\bpermission\s+(denied|error|failed)\b', re.IGNORECASE), "permission denied pattern"),
            (PERMISSION_ERROR, re.compile(r'\baccess\s+(denied|forbidden|refused)\b', re.IGNORECASE), "access denied pattern"),
            (PERMISSION_ERROR, re.compile(r'\b(cannot|could\s+not|unable\s+to)\s+(write|create|delete|modify|access)\b', re.IGNORECASE), "cannot write/create pattern"),
            (PERMISSION_ERROR, re.compile(r'\binsufficient\s+permissions|read\s+only|write\s+protected\b', re.IGNORECASE), "insufficient permissions pattern"),
            
            # Resource errors - expanded
            (RESOURCE_ERROR, re.compile(r'\bout\s+of\s+memory|oom|memory\s+(error|exhausted|limit)\b', re.IGNORECASE), "out of memory pattern"),
            (RESOURCE_ERROR, re.compile(r'\bdisk\s+(full|space|quota)|no\s+space\s+left\b', re.IGNORECASE), "disk full pattern"),
            (RESOURCE_ERROR, re.compile(r'\bresource\s+(exhausted|limit|quota|error)\b', re.IGNORECASE), "resource exhausted pattern"),
            (RESOURCE_ERROR, re.compile(r'\bcannot\s+allocate|allocation\s+failed|quota\s+exceeded\b', re.IGNORECASE), "allocation failed pattern"),
            
            # Lint errors
            (LINT_ERROR, re.compile(r'\blint.*(error|failed|failure|warning)\b', re.IGNORECASE), "lint error pattern"),
            (LINT_ERROR, re.compile(r'\blinting\s+(failed|error)|code\s+style\s+error\b', re.IGNORECASE), "linting failed pattern"),
            
            # Java exceptions - more comprehensive
            (BUILD_ERROR, re.compile(r'\bjava\.lang\.(nullpointer|illegalstate|illegalargument|classnotfound|runtime|indexoutofbounds)exception\b', re.IGNORECASE), "Java runtime exception pattern"),
            (BUILD_ERROR, re.compile(r'\b(nullpointer|illegalstate|illegalargument|classnotfound|runtime|indexoutofbounds)exception\b', re.IGNORECASE), "Java exception pattern"),
            (BUILD_ERROR, re.compile(r'\bjava\.(sql|io|util|net)\..*exception\b', re.IGNORECASE), "Java library exception pattern"),
            
            # Python exceptions - more comprehensive
            (BUILD_ERROR, re.compile(r'\b(attribute|value|type|key|index|name|runtime|io|os)error\b', re.IGNORECASE), "Python exception pattern"),
            (BUILD_ERROR, re.compile(r'\bpython.*(attribute|value|type|key|index|name)error\b', re.IGNORECASE), "Python error pattern"),
            
            # Generic exception patterns (catch-all for unhandled exceptions)
            (BUILD_ERROR, re.compile(r'\b(unhandled|unexpected|uncaught).*\s+exception\b', re.IGNORECASE), "unhandled exception pattern"),
            (BUILD_ERROR, re.compile(r'\bexception\s+(occurred|thrown|raised|failed)\b', re.IGNORECASE), "exception occurred pattern"),
        ]
    
    def classify(self, error_entry: Dict[str, str], context: Optional[List[Dict[str, str]]] = None) -> Dict[str, str]:
        """
        Classify an error entry into a category with sophisticated multi-field analysis.
        
        Args:
            error_entry: Dictionary with 'message', 'level', 'line_number', etc. from extractor
            context: Optional list of surrounding error entries for context-aware classification
        
        Returns:
            Dictionary with:
                - 'category': Category string (e.g., TEST_FAILURE, NETWORK_ERROR, etc.)
                - 'line_number': Line number from the error entry
                - 'message': Original error message
                - 'level': Log level (ERROR, FATAL, etc.)
                - 'confidence': Confidence score (0.0-1.0) based on pattern strength
                - 'matched_pattern': The pattern that matched (for explainability)
        """
        message = error_entry.get('message', '')
        message_lower = message.lower()
        level = error_entry.get('level', '').upper()
        line_number = error_entry.get('line_number', '')
        
        # Multi-field analysis: combine message, level, and context
        best_match = None
        best_confidence = 0.0
        matched_pattern = None
        
        # Check patterns with confidence scoring
        for category, pattern, description in self.patterns:
            match = pattern.search(message_lower)
            if match:
                # Base confidence from pattern position (earlier = more specific = higher confidence)
                pattern_index = self.patterns.index((category, pattern, description))
                base_confidence = 1.0 - (pattern_index * 0.01)  # Earlier patterns get higher confidence
                base_confidence = max(0.5, base_confidence)  # Minimum 50% confidence
                
                # Boost confidence based on log level
                level_boost = 0.0
                if level in ['FATAL', 'CRITICAL']:
                    level_boost = 0.2
                elif level == 'ERROR':
                    level_boost = 0.1
                
                # Context-aware boost (if surrounding errors match same category)
                context_boost = 0.0
                if context:
                    context_boost = self._calculate_context_boost(category, context)
                
                confidence = min(1.0, base_confidence + level_boost + context_boost)
                
                # Take the first match (most specific pattern wins)
                if best_match is None or confidence > best_confidence:
                    best_match = category
                    best_confidence = confidence
                    matched_pattern = description
                    self.pattern_stats[f"{category}:{description}"] += 1
                    break  # First match wins (most specific)
        
        # If no pattern matched, check for context clues
        if best_match is None and context:
            best_match = self._classify_from_context(context)
            if best_match:
                best_confidence = 0.6  # Lower confidence for context-based classification
                matched_pattern = "context-based"
        
        # Default to OTHER if no pattern matches
        if best_match is None:
            best_match = OTHER
            best_confidence = 0.3  # Low confidence for unclassified
            matched_pattern = "none"
            logger.debug(f"No pattern matched, defaulting to OTHER: {message[:50]}...")
        else:
            logger.debug(f"Classified as {best_match} (confidence: {best_confidence:.2f}): {message[:50]}...")
        
        self.category_stats[best_match] += 1
        
        return {
            'category': best_match,
            'line_number': line_number,
            'message': message,
            'level': level,
            'confidence': round(best_confidence, 2),
            'matched_pattern': matched_pattern if matched_pattern else "none"
        }
    
    def _calculate_context_boost(self, category: str, context: List[Dict[str, str]]) -> float:
        """
        Calculate confidence boost based on surrounding error context.
        
        If surrounding errors are the same category, increase confidence.
        """
        if not context:
            return 0.0
        
        # Check if any context errors match the same category
        context_matches = 0
        for ctx_error in context[-3:]:  # Check last 3 context errors
            ctx_message = ctx_error.get('message', '').lower()
            for cat, pattern, _ in self.patterns:
                if cat == category and pattern.search(ctx_message):
                    context_matches += 1
                    break
        
        # Boost confidence if context matches (up to 0.15)
        return min(0.15, context_matches * 0.05)
    
    def _classify_from_context(self, context: List[Dict[str, str]]) -> Optional[str]:
        """
        Attempt to classify based on surrounding context when direct pattern match fails.
        """
        if not context:
            return None
        
        # Look at recent context errors to infer category
        for ctx_error in reversed(context[-5:]):  # Check last 5 context errors
            ctx_message = ctx_error.get('message', '').lower()
            for category, pattern, _ in self.patterns:
                if pattern.search(ctx_message):
                    return category
        
        return None
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get classification statistics for analysis and debugging.
        
        Returns:
            Dictionary with pattern usage stats and category distribution
        """
        return {
            'pattern_usage': dict(self.pattern_stats),
            'category_distribution': dict(self.category_stats),
            'total_classifications': sum(self.category_stats.values())
        }
    
    def classify_batch(self, error_entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Classify multiple error entries with context awareness.
        
        Args:
            error_entries: List of error entry dictionaries
        
        Returns:
            List of classified error dictionaries with confidence scores
        """
        classified = []
        context = []
        
        for error_entry in error_entries:
            # Classify with context from previous errors
            result = self.classify(error_entry, context)
            classified.append(result)
            
            # Add to context (keep last 10 for context window)
            context.append(error_entry)
            if len(context) > 10:
                context.pop(0)
        
        return classified