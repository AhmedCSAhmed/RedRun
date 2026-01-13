"""
Error category constants for classification.

This module defines the standard error categories used by the Classifier
to categorize extracted errors from CI build logs. Each category represents
a distinct type of failure that can occur in CI/CD pipelines.

Categories are designed to be:
- Mutually exclusive: Each error should map to one primary category
- Actionable: Categories suggest specific remediation strategies
- Comprehensive: Cover common failure modes in CI/CD environments

These constants are used throughout the classification pipeline to ensure
consistent category naming and to avoid magic strings in the codebase.
"""

# Original categories
TEST_FAILURE = "Test Failure"
"""Category for test execution failures (unit tests, integration tests, etc.)."""

DEPENDENCY_FAILURE = "Dependency Error"
"""Category for dependency resolution and package management failures."""

INFRA_TIMEOUT = "Infrastructure Timeout"
"""Category for timeout-related failures (network timeouts, operation timeouts, etc.)."""

BUILD_ERROR = "Build Error"
"""Category for compilation, build, and code-level errors (syntax errors, type errors, etc.)."""

LINT_ERROR = "Lint Error"
"""Category for linting and code style check failures."""

AUTH_ERROR = "Authentication Error"
"""Category for authentication and authorization failures."""

PERMISSION_ERROR = "Permission Error"
"""Category for file system and resource permission failures."""

NETWORK_ERROR = "Network Error"
"""Category for network-related failures (connection refused, DNS errors, etc.)."""

CONFIG_ERROR = "Configuration Error"
"""Category for configuration and environment variable failures."""

DB_ERROR = "Database Error"
"""Category for database connection and query failures."""

RESOURCE_ERROR = "Resource Error"
"""Category for resource exhaustion failures (memory, disk space, quotas, etc.)."""

# New categories
INFRASTRUCTURE_ERROR = "Infrastructure Error"
"""Category for infrastructure-related failures (network, database, configuration, etc.)."""

COMPILATION_ERROR = "Compilation Error"
"""Category for compilation and code-level errors (syntax errors, type errors, etc.)."""

RUNTIME_ERROR = "Runtime Error"
"""Category for runtime exceptions and errors during execution."""

TIMEOUT = "Timeout"
"""Category for timeout-related failures (network timeouts, operation timeouts, etc.)."""

SECURITY_PERMISSION_ERROR = "Security / Permission Error"
"""Category for authentication, authorization, and permission failures."""

TOOLING_ERROR = "Tooling Error"
"""Category for tooling failures (linting, dependency resolution, package managers, etc.)."""

CONFIGURATION_ERROR = "Configuration Error"
"""Category for configuration-related failures (config file errors, missing config, invalid settings, etc.)."""

AUTHENTICATION_ERROR = "Authentication Error"
"""Category for authentication failures (invalid credentials, token issues, auth service failures, etc.)."""

AVAILABILITY_ERROR = "Availability Error"
"""Category for service availability and health check failures (liveness checks, service unavailable, etc.)."""

OTHER = "Other"
"""Category for errors that don't match any specific pattern or are unclassified."""