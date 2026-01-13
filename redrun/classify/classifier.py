"""
Error classification module.

This module provides the Classifier class which categorizes extracted
errors into actionable categories using rule-based pattern matching.
The classifier uses sophisticated features including:
- Confidence scoring based on pattern specificity and log level
- Context-aware classification using surrounding log entries
- Pattern performance tracking for analysis and debugging

The classification is deterministic and explainable, making it suitable
for CI/CD environments where understanding why an error was classified
a certain way is important.
"""

from typing import Dict, List, Tuple, Optional
import re
import logging
from collections import defaultdict
from .categories import (
    TEST_FAILURE, DEPENDENCY_FAILURE, INFRA_TIMEOUT, BUILD_ERROR,
    LINT_ERROR, AUTH_ERROR, PERMISSION_ERROR, NETWORK_ERROR,
    CONFIG_ERROR, DB_ERROR, RESOURCE_ERROR,
    INFRASTRUCTURE_ERROR, COMPILATION_ERROR, RUNTIME_ERROR, TIMEOUT,
    SECURITY_PERMISSION_ERROR, TOOLING_ERROR,
    CONFIGURATION_ERROR, AUTHENTICATION_ERROR, AVAILABILITY_ERROR,
    OTHER
)

logger = logging.getLogger(__name__)


class Classifier:
    """
    Classifies error entries into categories using pattern matching.
    
    Takes extracted error entries and categorizes them based on message
    patterns. Uses deterministic rule-based matching for explainability.
    """
    
    def __init__(self):
        # Track pattern usage and category distribution for statistics
        self.pattern_stats = defaultdict(int)
        self.category_stats = defaultdict(int)
        
        # Patterns are ordered by specificity: more specific patterns come first
        # First match wins, so order matters for classification accuracy
        self.patterns = [
            # Test failures: framework errors, assertions, test file patterns
            (TEST_FAILURE, re.compile(r'\b(junit|testng|pytest|jest|mocha).*\s+(failed|failure|error)\b', re.IGNORECASE), "test_framework_error"),
            (TEST_FAILURE, re.compile(r'\bassertion\s*(error|failed|failure)\b', re.IGNORECASE), "test_assertion_failure"),
            (TEST_FAILURE, re.compile(r'\btest\s+(failed|failure|failures|failing)\b', re.IGNORECASE), "test_failure_generic"),
            (TEST_FAILURE, re.compile(r'\btest\s+.*\s+(failed|failure|error)\b', re.IGNORECASE), "test_execution_error"),
            (TEST_FAILURE, re.compile(r'\.test\.|Test.*\.(java|kt|scala)|.*Test\.(py|js|ts)', re.IGNORECASE), "test_file_reference"),
            (TEST_FAILURE, re.compile(r'\btest\s+suite.*(failed|error|exception)\b', re.IGNORECASE), "test_suite_failure"),
            (TEST_FAILURE, re.compile(r'\b(test|tests)\s+(are|is)\s+(failing|broken)\b', re.IGNORECASE), "test_status_failure"),
            
            
            # Compilation errors: syntax, parsing, unresolved references, type errors
            (COMPILATION_ERROR, re.compile(r'\bsyntax\s+error|parse\s+error|compilation\s+error\b', re.IGNORECASE), "syntax_parse_error"),
            (COMPILATION_ERROR, re.compile(r'\b(compilation|compile).*\s+(error|failed|failure)\b', re.IGNORECASE), "compilation_failure"),
            (COMPILATION_ERROR, re.compile(r'\bcannot\s+resolve|could\s+not\s+resolve|unresolved\b', re.IGNORECASE), "unresolved_symbol"),
            (COMPILATION_ERROR, re.compile(r'\bpackage.*not\s+found|class.*not\s+found|module.*not\s+found\b', re.IGNORECASE), "missing_dependency"),
            (COMPILATION_ERROR, re.compile(r'\btype\s+error|type\s+mismatch|type\s+check\s+failed\b', re.IGNORECASE), "type_check_error"),
            
            
            # Build errors: schema mismatches, build process failures
            (BUILD_ERROR, re.compile(r'\brelation\s+.*\s+does\s+not\s+exist\b', re.IGNORECASE), "missing_db_relation"),
            (BUILD_ERROR, re.compile(r'\bcolumn\s+.*\s+does\s+not\s+exist\b', re.IGNORECASE), "schema_mismatch"),
            (BUILD_ERROR, re.compile(r'\bbuild\s+(failed|failure|error|broken)\b', re.IGNORECASE), "build_failure"),
            (BUILD_ERROR, re.compile(r'\bbuild\s+.*\s+(failed|error|aborted|stopped)\b', re.IGNORECASE), "build_process_error"),
            
            
            # Runtime errors: user application logic bugs (not infrastructure or tooling)
            (RUNTIME_ERROR, re.compile(r'\bduplicate\s+key.*violation\b', re.IGNORECASE), "duplicate_key_violation"),
            (RUNTIME_ERROR, re.compile(r'\bduplicate\s+key\s+value\b', re.IGNORECASE), "duplicate_key_value"),
            (RUNTIME_ERROR, re.compile(r'\bviolates\s+foreign\s+key\s+constraint\b', re.IGNORECASE), "foreign_key_violation"),
            (RUNTIME_ERROR, re.compile(r'\bdetachedinstanceerror\b', re.IGNORECASE), "orm_detached_instance"),
            (RUNTIME_ERROR, re.compile(r'\bdetached\s+instance\b', re.IGNORECASE), "orm_session_error"),
            
            
            # Security/permission errors: auth failures, SSL certs, access control
            (SECURITY_PERMISSION_ERROR, re.compile(r'\bsslhandshakeexception\b', re.IGNORECASE), "ssl_handshake_exception"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\bssl\s+handshake\s+(failed|error|exception)\b', re.IGNORECASE), "ssl_handshake_failure"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\bcertificate\s+verify\s+failed|certificate_verify_failed\b', re.IGNORECASE), "ssl_cert_verify_failed"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\bssl.*certificate.*(error|failed|invalid|verify)\b', re.IGNORECASE), "ssl_cert_error"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\bauthentication\s+(failed|error|failure|denied)\b', re.IGNORECASE), "auth_failure"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\bunauthorized|auth\s+(error|failed|failure)\b', re.IGNORECASE), "unauthorized"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\binvalid\s+(credentials|token|password|api\s+key)\b', re.IGNORECASE), "invalid_credentials"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\btoken\s+(expired|invalid|missing)|session\s+expired\b', re.IGNORECASE), "token_expired"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\bpermission\s+(denied|error|failed)\b', re.IGNORECASE), "permission_denied"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\baccess\s+(denied|forbidden|refused)\b', re.IGNORECASE), "access_denied"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\b(cannot|could\s+not|unable\s+to)\s+(write|create|delete|modify|access)\b', re.IGNORECASE), "filesystem_permission"),
            (SECURITY_PERMISSION_ERROR, re.compile(r'\binsufficient\s+permissions|read\s+only|write\s+protected\b', re.IGNORECASE), "insufficient_permissions"),
            
            
            # Authentication errors: auth failures, token issues, credentials
            (AUTHENTICATION_ERROR, re.compile(r'\bpermissiondeniedexception\b', re.IGNORECASE), "permission_denied_exception"),
            (AUTHENTICATION_ERROR, re.compile(r'\bacl\s+token.*(error|failed|failure|invalid|missing|expired)\b', re.IGNORECASE), "acl_token_error"),
            (AUTHENTICATION_ERROR, re.compile(r'\bjwt\s+public\s+key.*(error|failed|failure|invalid|missing|not\s+found)\b', re.IGNORECASE), "jwt_public_key_error"),
            (AUTHENTICATION_ERROR, re.compile(r'\binvalid\s+token\b', re.IGNORECASE), "invalid_token"),
            (AUTHENTICATION_ERROR, re.compile(r'\b401\b|\bhttp\s+401\b|status\s+code\s+401\b', re.IGNORECASE), "http_401_unauthorized"),
            
            
            # Configuration errors: config file issues, refresh failures
            (CONFIGURATION_ERROR, re.compile(r'\bconfig\s+refresh\s+failed\b', re.IGNORECASE), "config_refresh_failed"),
            
            
            # Availability errors: health checks, liveness, service availability
            (AVAILABILITY_ERROR, re.compile(r'\brequest\s+failed\s+after\s+retries\b', re.IGNORECASE), "request_failed_retries"),
            (AVAILABILITY_ERROR, re.compile(r'\breturning\s+503\b', re.IGNORECASE), "returning_503"),
            (AVAILABILITY_ERROR, re.compile(r'\bservice\s+unavailable\b', re.IGNORECASE), "service_unavailable"),
            (AVAILABILITY_ERROR, re.compile(r'\b503\s+(error|failed|failure|unavailable)\b', re.IGNORECASE), "http_503"),
            (AVAILABILITY_ERROR, re.compile(r'\bhttp\s+503\b|status\s+code\s+503\b', re.IGNORECASE), "http_status_503"),
            (AVAILABILITY_ERROR, re.compile(r'\bliveness\s+check\s+failed\b', re.IGNORECASE), "liveness_check_failed"),
            
            
            # Timeouts: operation timeouts, time limit violations, rate limits
            (TIMEOUT, re.compile(r'\brate\s+limit\s+exceeded\b', re.IGNORECASE), "rate_limit_exceeded"),
            (TIMEOUT, re.compile(r'\b(ratelimiterror|rate.*limit).*\s+(exceeded|reached|hit)\b', re.IGNORECASE), "rate_limit_error"),
            (TIMEOUT, re.compile(r'\b(request|operation|connection|health\s+check|container).*\s+timeout\b', re.IGNORECASE), "operation_timeout"),
            (TIMEOUT, re.compile(r'\bexceeded.*time.*limit|time.*limit.*exceeded\b', re.IGNORECASE), "time_limit_exceeded"),
            (TIMEOUT, re.compile(r'\b(timeout|timed\s+out|time\s+out)\b', re.IGNORECASE), "timeout_generic"),
            
            
            # Tooling errors: internal tool failures, linters, package managers, build tools
            (TOOLING_ERROR, re.compile(r'\b(stackanalyzer|stacktraceextractor|rootcauseengine).*\s+(error|failed|failure|exception)\b', re.IGNORECASE), "internal_tool_failure"),
            (TOOLING_ERROR, re.compile(r'\brootcauseengine.*\s+(error|failed|failure|exception)\b', re.IGNORECASE), "rootcause_engine_failure"),
            (TOOLING_ERROR, re.compile(r'\b(analyzer|logparser).*\s+(error|failed|failure|exception)\b', re.IGNORECASE), "analyzer_failure"),
            (TOOLING_ERROR, re.compile(r'\bfailed\s+to\s+parse\s+stack\s+trace\b', re.IGNORECASE), "stack_parse_failure"),
            (TOOLING_ERROR, re.compile(r'\bmalformed\s+stack\s+trace\b', re.IGNORECASE), "malformed_stack_trace"),
            (TOOLING_ERROR, re.compile(r'\bnull\s+pointer.*(during|while).*classification\b', re.IGNORECASE), "root_cause_engine_npe"),
            (TOOLING_ERROR, re.compile(r'\bnull\s+pointer.*computing.*failure\s+signature\b', re.IGNORECASE), "root_cause_engine_npe_alt"),
            (TOOLING_ERROR, re.compile(r'\billegalargumentexception.*malformed\s+stack\s+trace\b', re.IGNORECASE), "parser_illegal_argument"),
            (TOOLING_ERROR, re.compile(r'\b(stack|trace|log).*parser.*\s+(error|failed|failure|exception)\b', re.IGNORECASE), "log_parser_failure"),
            (TOOLING_ERROR, re.compile(r'\bunexpected\s+token.*\s+at\s+line\b', re.IGNORECASE), "parser_syntax_error"),
            (TOOLING_ERROR, re.compile(r'\blint.*(error|failed|failure|warning)\b', re.IGNORECASE), "lint_error"),
            (TOOLING_ERROR, re.compile(r'\blinting\s+(failed|error)|code\s+style\s+error\b', re.IGNORECASE), "linting_failure"),
            (TOOLING_ERROR, re.compile(r'\b(maven|gradle|npm|pip|yarn|pypi|composer|nuget|go\s+mod).*\s+(error|failed|failure)\b', re.IGNORECASE), "package_manager_error"),
            (TOOLING_ERROR, re.compile(r'\bdependency.*(error|failed|failure|missing|not\s+found)\b', re.IGNORECASE), "dependency_error"),
            (TOOLING_ERROR, re.compile(r'\bcannot\s+resolve.*dependency|failed\s+to\s+resolve\b', re.IGNORECASE), "dependency_resolution_failure"),
            (TOOLING_ERROR, re.compile(r'\bversion\s+conflict|dependency\s+conflict|conflicting\s+dependencies\b', re.IGNORECASE), "version_conflict"),
            (TOOLING_ERROR, re.compile(r'\b(eslint|pylint|flake8|black|prettier|rubocop|gofmt).*\s+(error|failed|failure)\b', re.IGNORECASE), "code_formatter_error"),
            (TOOLING_ERROR, re.compile(r'\b(make|cmake|ant|sbt|leiningen).*\s+(error|failed|failure)\b', re.IGNORECASE), "build_tool_error"),
            
            
            # Infrastructure errors: external services, CI/CD, network, configuration
            (INFRASTRUCTURE_ERROR, re.compile(r'\bci\s+executor.*lost\s+heartbeat\b', re.IGNORECASE), "ci_executor_heartbeat_lost"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\bexecutor.*lost\s+heartbeat|heartbeat.*lost\b', re.IGNORECASE), "executor_heartbeat_lost"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\bcontainer.*(oomkilled|oom.*killed)\b', re.IGNORECASE), "container_oom_killed"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\bcontainer\s+terminated\b', re.IGNORECASE), "container_terminated"),
            
            
            # Resource errors: memory/disk exhaustion, process kills, connection pools
            (RESOURCE_ERROR, re.compile(r'\bheap\s+usage\s+critical\b', re.IGNORECASE), "heap_usage_critical"),
            (RESOURCE_ERROR, re.compile(r'\bto-space\s+exhausted\b', re.IGNORECASE), "to_space_exhausted"),
            (RESOURCE_ERROR, re.compile(r'\bGC\s+(error|failed|failure|exhausted|critical)\b', re.IGNORECASE), "gc_error"),
            (RESOURCE_ERROR, re.compile(r'\bgarbage\s+collection.*(error|failed|failure|exhausted|critical)\b', re.IGNORECASE), "garbage_collection_error"),
            (RESOURCE_ERROR, re.compile(r'\bOutOfMemory\b', re.IGNORECASE), "out_of_memory_exception"),
            (RESOURCE_ERROR, re.compile(r'\bOOMKilled\b', re.IGNORECASE), "oom_killed"),
            (RESOURCE_ERROR, re.compile(r'\bMemoryMonitor.*(error|failed|failure|critical|exhausted)\b', re.IGNORECASE), "memory_monitor_error"),
            (RESOURCE_ERROR, re.compile(r'\bexited\s+with\s+code\s+137\b', re.IGNORECASE), "exit_code_137"),
            (RESOURCE_ERROR, re.compile(r'\bexit\s+code\s+137\b', re.IGNORECASE), "exit_code_137_alt"),
            (RESOURCE_ERROR, re.compile(r'\bcuda\s+out\s+of\s+memory|cuda\s+oom\b', re.IGNORECASE), "cuda_oom"),
            (RESOURCE_ERROR, re.compile(r'\bsigkill|killed\s+by\s+signal\s+9\b', re.IGNORECASE), "sigkill"),
            (RESOURCE_ERROR, re.compile(r'\bconnection\s+pool\s+exhausted\b', re.IGNORECASE), "connection_pool_exhausted"),
            (RESOURCE_ERROR, re.compile(r'\bmemory\s+pressure\s+(critical|high)\b', re.IGNORECASE), "memory_pressure"),
            (RESOURCE_ERROR, re.compile(r'\bmemory\s+pressure\b', re.IGNORECASE), "memory_pressure_generic"),
            (RESOURCE_ERROR, re.compile(r'\btriggering\s+graceful\s+shutdown\b', re.IGNORECASE), "graceful_shutdown_memory"),
            (RESOURCE_ERROR, re.compile(r'\bout\s+of\s+memory\b', re.IGNORECASE), "out_of_memory"),
            (RESOURCE_ERROR, re.compile(r'\bmemory\s+(error|exhausted|limit)\b', re.IGNORECASE), "memory_error"),
            (RESOURCE_ERROR, re.compile(r'\bdisk\s+(full|space|quota)|no\s+space\s+left\b', re.IGNORECASE), "disk_full"),
            (RESOURCE_ERROR, re.compile(r'\bsystem\s+resource\s+(exhausted|limit|quota)\b', re.IGNORECASE), "system_resource_exhausted"),
            (RESOURCE_ERROR, re.compile(r'\bcannot\s+allocate|allocation\s+failed|quota\s+exceeded\b', re.IGNORECASE), "allocation_failed"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\bkafka.*failed\s+to\s+publish\s+event\b', re.IGNORECASE), "kafka_publish_failure"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\bkafka.*failed\s+to\s+send\s+message\b', re.IGNORECASE), "kafka_send_failure"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\b(kafka|zookeeper).*\s+metadata.*timeout\b', re.IGNORECASE), "kafka_metadata_timeout"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\btopic.*not\s+present\s+in\s+metadata\b', re.IGNORECASE), "kafka_topic_missing"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\btimeoutexception.*topic.*not\s+present\s+in\s+metadata\b', re.IGNORECASE), "kafka_timeout_topic_missing"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\bconnection\s+(refused|reset|closed|dropped|failed)\b', re.IGNORECASE), "connection_failure"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\bdatabase\s+connection\s+(failed|error|lost|refused)\b', re.IGNORECASE), "database_connection_failure"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\b(redis|postgres|mysql|mongodb|elasticsearch).*\s+connection\s+(refused|failed|error)\b', re.IGNORECASE), "service_connection_failure"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\b(dns|hostname|resolve).*\s+(error|failed|unreachable|not\s+found)\b', re.IGNORECASE), "dns_resolution_failure"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\b(network|socket|http|tcp|udp)\s+.*\s+(error|exception|failure|unreachable)\b', re.IGNORECASE), "network_protocol_error"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\b(peer|server|client)\s+.*\s+(reset|refused|closed|unreachable)\b', re.IGNORECASE), "peer_connection_failure"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\bservice\s+(unavailable|down|unreachable|not\s+found)\b', re.IGNORECASE), "service_unavailable"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\brequired\s+.*\s+(configuration|config|value|setting|parameter).*\s+missing\b', re.IGNORECASE), "config_missing"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\b(config|configuration|setting).*\s+(error|missing|invalid|not\s+found)\b', re.IGNORECASE), "config_error"),
            (INFRASTRUCTURE_ERROR, re.compile(r'\benvironment\s+variable.*missing|env\s+var.*not\s+set\b', re.IGNORECASE), "env_var_missing"),
            
            
            # Database errors - SQL exceptions always map here (no exceptions)
            # Catch-all rule: if message contains org.postgresql, SQLSTATE, serialize, or recovery → always DB_ERROR
            (DB_ERROR, re.compile(r'\borg\.postgresql\b', re.IGNORECASE), "postgresql_exception_catchall"),
            (DB_ERROR, re.compile(r'\bSQLSTATE\b', re.IGNORECASE), "sqlstate_catchall"),
            (DB_ERROR, re.compile(r'\bserializ(e|ation)\b', re.IGNORECASE), "serialize_catchall"),
            (DB_ERROR, re.compile(r'\brecovery\b', re.IGNORECASE), "recovery_catchall"),
            (DB_ERROR, re.compile(r'\btransaction\s+commit\s+failed\b', re.IGNORECASE), "transaction_commit_failed"),
            (DB_ERROR, re.compile(r'\bpsqlexception\b', re.IGNORECASE), "postgresql_exception"),
            (DB_ERROR, re.compile(r'\bpostgresql.*exception\b', re.IGNORECASE), "postgresql_error"),
            (DB_ERROR, re.compile(r'\bcanceling\s+statement\b', re.IGNORECASE), "statement_canceled"),
            (DB_ERROR, re.compile(r'\bwrite\s+aborted\s+after\s+retries\b', re.IGNORECASE), "write_aborted_retries"),
            (DB_ERROR, re.compile(r'\bserialization\s+failure\b', re.IGNORECASE), "concurrency_serialization"),
            (DB_ERROR, re.compile(r'\bcould\s+not\s+serialize\s+access\b', re.IGNORECASE), "concurrent_update_serialization"),
            (DB_ERROR, re.compile(r'\bcanceling\s+statement\s+due\s+to\s+conflict\s+with\s+recovery\b', re.IGNORECASE), "recovery_conflict"),
            (DB_ERROR, re.compile(r'\b(sql|database|db)\s+.*\s+(exception|error|failure)\b', re.IGNORECASE), "database_error"),
            (DB_ERROR, re.compile(r'\b(hikari.*pool|jdbc|datasource)\b', re.IGNORECASE), "connection_pool_ref"),
            (DB_ERROR, re.compile(r'\bconnection\s+(is\s+)?not\s+available\b', re.IGNORECASE), "connection_unavailable"),
            (DB_ERROR, re.compile(r'\b(query|transaction|sql)\s+timeout\b', re.IGNORECASE), "query_timeout"),
            (DB_ERROR, re.compile(r'\b(deadlock|lock\s+timeout|connection\s+refused)\b', re.IGNORECASE), "deadlock"),
            (DB_ERROR, re.compile(r'\bsql(transient|timeout|connection)?exception\b', re.IGNORECASE), "sql_exception"),
            (DB_ERROR, re.compile(r'\bdatabase\s+connection\s+(failed|error|lost)\b', re.IGNORECASE), "database_connection_failure"),
            
            
            # Network errors 
            (NETWORK_ERROR, re.compile(r'\bconnection\s+(reset|refused|closed|dropped|failed)\b', re.IGNORECASE), "connection_failure"),
            (NETWORK_ERROR, re.compile(r'\b(network|socket|http|tcp|udp)\s+.*\s+(error|exception|failure)\b', re.IGNORECASE), "network_protocol_error"),
            (NETWORK_ERROR, re.compile(r'\bconnection\s+timeout|network\s+unreachable\b', re.IGNORECASE), "network_timeout"),
            (NETWORK_ERROR, re.compile(r'\b(dns|hostname|resolve).*\s+(error|failed|unreachable)\b', re.IGNORECASE), "dns_resolution_failure"),
            (NETWORK_ERROR, re.compile(r'\b(connection|network|socket)\s+.*\s+(error|exception)\b', re.IGNORECASE), "network_error"),
            (NETWORK_ERROR, re.compile(r'\b(peer|server|client)\s+.*\s+(reset|refused|closed)\b', re.IGNORECASE), "peer_connection_failure"),
            
            
            # Configuration errors 
            (CONFIG_ERROR, re.compile(r'\brequired\s+.*\s+(configuration|config|value|setting|parameter).*\s+missing\b', re.IGNORECASE), "config_missing"),
            (CONFIG_ERROR, re.compile(r'\b(config|configuration|setting).*\s+(error|missing|invalid|not\s+found)\b', re.IGNORECASE), "config_error"),
            (CONFIG_ERROR, re.compile(r'\benvironment\s+variable.*missing|env\s+var.*not\s+set\b', re.IGNORECASE), "env_var_missing"),
            (CONFIG_ERROR, re.compile(r'\billegalstateexception.*required|required.*value.*missing\b', re.IGNORECASE), "required_value_missing"),
            (CONFIG_ERROR, re.compile(r'\b(missing|invalid|incorrect).*\s+(config|configuration|setting)\b', re.IGNORECASE), "config_invalid"),
            
            
            # Infrastructure timeouts 
            (INFRA_TIMEOUT, re.compile(r'\b(timeout|timed\s+out|time\s+out)\b', re.IGNORECASE), "timeout_generic"),
            (INFRA_TIMEOUT, re.compile(r'\b(request|operation|connection|health\s+check|container).*\s+timeout\b', re.IGNORECASE), "operation_timeout"),
            (INFRA_TIMEOUT, re.compile(r'\bexceeded.*time.*limit|time.*limit.*exceeded\b', re.IGNORECASE), "time_limit_exceeded"),
            
            
            # Dependency errors 
            (DEPENDENCY_FAILURE, re.compile(r'\bdependency.*(error|failed|failure|missing|not\s+found)\b', re.IGNORECASE), "dependency_error"),
            (DEPENDENCY_FAILURE, re.compile(r'\bpackage.*not\s+found|module.*not\s+found|library.*missing\b', re.IGNORECASE), "package_missing"),
            (DEPENDENCY_FAILURE, re.compile(r'\b(maven|gradle|npm|pip|yarn).*\s+(error|failed|failure)\b', re.IGNORECASE), "package_manager_error"),
            (DEPENDENCY_FAILURE, re.compile(r'\bcannot\s+resolve.*dependency|failed\s+to\s+resolve\b', re.IGNORECASE), "dependency_resolution_failure"),
            (DEPENDENCY_FAILURE, re.compile(r'\bversion\s+conflict|dependency\s+conflict|conflicting\s+dependencies\b', re.IGNORECASE), "version_conflict"),
            
            
            # Authentication errors 
            (AUTH_ERROR, re.compile(r'\bauthentication\s+(failed|error|failure|denied)\b', re.IGNORECASE), "auth_failure"),
            (AUTH_ERROR, re.compile(r'\bunauthorized|auth\s+(error|failed|failure)\b', re.IGNORECASE), "unauthorized"),
            (AUTH_ERROR, re.compile(r'\binvalid\s+(credentials|token|password|api\s+key)\b', re.IGNORECASE), "invalid_credentials"),
            (AUTH_ERROR, re.compile(r'\btoken\s+(expired|invalid|missing)|session\s+expired\b', re.IGNORECASE), "token_expired"),
            
            
            # Permission errors 
            (PERMISSION_ERROR, re.compile(r'\bpermission\s+(denied|error|failed)\b', re.IGNORECASE), "permission_denied"),
            (PERMISSION_ERROR, re.compile(r'\baccess\s+(denied|forbidden|refused)\b', re.IGNORECASE), "access_denied"),
            (PERMISSION_ERROR, re.compile(r'\b(cannot|could\s+not|unable\s+to)\s+(write|create|delete|modify|access)\b', re.IGNORECASE), "filesystem_permission"),
            (PERMISSION_ERROR, re.compile(r'\binsufficient\s+permissions|read\s+only|write\s+protected\b', re.IGNORECASE), "insufficient_permissions"),
            
            # Lint errors 
            (LINT_ERROR, re.compile(r'\blint.*(error|failed|failure|warning)\b', re.IGNORECASE), "lint_error"),
            (LINT_ERROR, re.compile(r'\blinting\s+(failed|error)|code\s+style\s+error\b', re.IGNORECASE), "linting_failure"),
            
            # Generic summary lines: task/workflow failures that are summaries, not root causes
            (OTHER, re.compile(r'\btask\s+failed\s+permanently\b', re.IGNORECASE), "task_failed_summary"),
            (OTHER, re.compile(r'\bworkflow\s+failed\s+permanently\b', re.IGNORECASE), "workflow_failed_summary"),
        ]
    
    def classify(self, error_entry: Dict[str, str], context: Optional[List[Dict[str, str]]] = None) -> Dict[str, str]:
        """
        Classify an error entry into a category with sophisticated multi-field analysis.
        
        Args:
            error_entry: Dictionary with 'message', 'level', 'line_number', etc. from extractor
            context: Optional list of surrounding error entries for context-aware classification
        
        Returns:
            Dictionary with:
                - 'category': Category string (e.g., TEST_FAILURE, INFRASTRUCTURE_ERROR, etc.)
                - 'line_number': Line number from the error entry
                - 'message': Original error message
                - 'level': Log level (ERROR, FATAL, etc.)
                - 'confidence': Confidence score (0.0-1.0) based on pattern strength
                - 'matched_pattern': The pattern that matched (for explainability)
        """
        try:
            message = error_entry.get('message', '')
            message_lower = message.lower()
            level = error_entry.get('level', '').upper()
            line_number = error_entry.get('line_number', '')
            
            best_match = None
            best_confidence = 0.0
            matched_pattern = None
            
            # Iterate through patterns in order (most specific first)
            try:
                for category, pattern, description in self.patterns:
                    try:
                        match = pattern.search(message_lower)
                        if match:
                            # Base confidence decreases with pattern position (earlier = more specific = higher confidence)
                            pattern_index = self.patterns.index((category, pattern, description))
                            base_confidence = 1.0 - (pattern_index * 0.01)
                            base_confidence = max(0.5, base_confidence)  # Minimum 50% confidence
                            
                            # Boost confidence based on log level severity
                            level_boost = 0.0
                            if level in ['FATAL', 'CRITICAL']:
                                level_boost = 0.2
                            elif level == 'ERROR':
                                level_boost = 0.1
                            
                            # Boost confidence if surrounding errors match same category (context-aware)
                            context_boost = 0.0
                            if context:
                                try:
                                    context_boost = self._calculate_context_boost(category, context)
                                except Exception as e:
                                    logger.warning(f"Error calculating context boost: {e}")
                            
                            confidence = min(1.0, base_confidence + level_boost + context_boost)
                            
                            # Take first match (most specific pattern wins)
                            if best_match is None or confidence > best_confidence:
                                best_match = category
                                best_confidence = confidence
                                matched_pattern = description
                                self.pattern_stats[f"{category}:{description}"] += 1
                                break  # First match wins, no need to check remaining patterns
                    except (AttributeError, TypeError, ValueError) as e:
                        logger.warning(f"Error matching pattern {description}: {e}, skipping")
                        continue
            except Exception as e:
                logger.error(f"Error during pattern matching: {e}")
            
            # Fallback: if no direct pattern match, try context-based classification
            if best_match is None and context:
                try:
                    best_match = self._classify_from_context(context)
                    if best_match:
                        best_confidence = 0.6  # Lower confidence for context-based classification
                        matched_pattern = "context-based"
                except Exception as e:
                    logger.warning(f"Error in context-based classification: {e}")
            
            # Default to OTHER if no pattern or context match found
            if best_match is None:
                best_match = OTHER
                best_confidence = 0.3  # Low confidence for unclassified errors
                matched_pattern = "none"
                logger.debug(f"No pattern matched, defaulting to OTHER: {message[:50]}...")
            else:
                logger.debug(f"Classified as {best_match} (confidence: {best_confidence:.2f}): {message[:50]}...")
            
            # Track category distribution for statistics
            try:
                self.category_stats[best_match] += 1
            except Exception as e:
                logger.warning(f"Error tracking category stats: {e}")
            
            # Build and return classification result
            try:
                return {
                    'category': best_match,
                    'line_number': line_number,
                    'message': message,
                    'level': level,
                    'confidence': round(best_confidence, 2),
                    'matched_pattern': matched_pattern if matched_pattern else "none"
                }
            except Exception as e:
                logger.error(f"Error building classification result: {e}")
                # Fallback return if result construction fails
                return {
                    'category': best_match if best_match else OTHER,
                    'line_number': str(line_number) if line_number else '',
                    'message': str(message) if message else '',
                    'level': str(level) if level else '',
                    'confidence': 0.1,
                    'matched_pattern': "error"
                }
        except (KeyError, AttributeError, TypeError) as e:
            logger.error(f"Error classifying error entry: {e}, entry: {error_entry}")
            # Return safe default classification on error
            return {
                'category': OTHER,
                'line_number': error_entry.get('line_number', ''),
                'message': error_entry.get('message', ''),
                'level': error_entry.get('level', ''),
                'confidence': 0.1,
                'matched_pattern': "error"
            }
    
    def _calculate_context_boost(self, category: str, context: List[Dict[str, str]]) -> float:
        """
        Calculate confidence boost based on surrounding error context.
        
        This method implements context-aware classification by checking if
        surrounding errors (from the context window) match the same category.
        If multiple recent errors are of the same category, it increases
        confidence in the classification, as errors often cluster by type.
        
        Args:
            category: The category being considered for classification.
            context: List of recent error entries (typically last 3-10 entries)
                    that provide context for the current error.
        
        Returns:
            Confidence boost value between 0.0 and 0.15. The boost is
            proportional to the number of matching context errors, with
            a maximum boost of 0.15 (15 percentage points).
        
        Note:
            This method checks the last 3 context errors to avoid excessive
            computation while still providing useful context information.
        """
        try:
            if not context:
                return 0.0 # No context == no boost
            
            # Checking the last 3 context errors for same category matches
            context_matches = 0
            for ctx_error in context[-3:]:
                try:
                    ctx_message = ctx_error.get('message', '').lower()
                    # Check if context error matches the same category
                    for cat, pattern, _ in self.patterns: 
                        if cat == category: # the previous errors catagory must match the current error catagory
                            try:
                                if pattern.search(ctx_message): 
                                    context_matches += 1 # if at least one  previous context erorr matches the same category then we boost the conifence 
                                    break
                            except Exception:
                                continue
                except (AttributeError, KeyError, TypeError):
                    continue
            
            # Boost confidence by 5% per matching context error, max 15%
            return min(0.15, context_matches * 0.05)
        except Exception:
            return 0.0
    
    def _classify_from_context(self, context: List[Dict[str, str]]) -> Optional[str]:
        """
        Attempt to classify based on surrounding context when direct pattern match fails.
        
        This method is used as a fallback when no pattern directly matches
        the error message. It examines recent context errors to infer the
        category, which is useful for errors that are part of a larger
        failure pattern but don't contain explicit category keywords.
        
        Args:
            context: List of recent error entries (typically last 5-10 entries)
                    that provide context for classification.
        
        Returns:
            Category string if a matching pattern is found in context, None otherwise.
            The category is determined by finding the first pattern match in
            the reversed context (most recent first).
        
        Note:
            This method checks the last 5 context errors in reverse order
            (most recent first) to find the most relevant classification.
        """
        try:
            if not context:
                return None
            
            # Check last 5 context errors in reverse order (most recent first)
            # This allows inferring category from surrounding errors when direct match fails
            for ctx_error in reversed(context[-5:]):
                try:
                    ctx_message = ctx_error.get('message', '').lower()
                    # Return first category that matches any pattern in context
                    for category, pattern, _ in self.patterns:
                        try:
                            if pattern.search(ctx_message): # if at least one  previous context erorr matches the same category then we return the category
                                return category
                        except Exception:
                            continue
                except (AttributeError, KeyError, TypeError):
                    continue
            
            return None
        except Exception:
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
        context = []  # Sliding window of recent errors for context-aware classification
        
        for error_entry in error_entries:
            try:
                # Classify with context from previous errors
                result = self.classify(error_entry, context)
                classified.append(result)
                
                # Maintain context window: keep last 10 errors for context
                context.append(error_entry)
                if len(context) > 10:
                    context.pop(0)  # Remove oldest error when window exceeds 10
            except Exception as e:
                logger.error(f"Error classifying entry in batch: {e}, entry: {error_entry}")
                # Adding safe default classification to maintain batch integrity
                classified.append({
                    'category': OTHER,
                    'line_number': error_entry.get('line_number', ''),
                    'message': error_entry.get('message', ''),
                    'level': error_entry.get('level', ''),
                    'confidence': 0.1,
                    'matched_pattern': "error"
                })
        
        return classified