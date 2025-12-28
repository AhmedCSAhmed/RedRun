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

# Test and Quality Assurance Failures
TEST_FAILURE = "Test Failure"
"""Category for test execution failures (unit tests, integration tests, etc.)."""

# Dependency and Build System Failures
DEPENDENCY_FAILURE = "Dependency Error"
"""Category for dependency resolution and package management failures."""

# Infrastructure and System Failures
INFRA_TIMEOUT = "Infrastructure Timeout"
"""Category for timeout-related failures (network timeouts, operation timeouts, etc.)."""

BUILD_ERROR = "Build Error"
"""Category for compilation, build, and code-level errors (syntax errors, type errors, etc.)."""

# Code Quality Failures
LINT_ERROR = "Lint Error"
"""Category for linting and code style check failures."""

# Security and Access Failures
AUTH_ERROR = "Authentication Error"
"""Category for authentication and authorization failures."""

PERMISSION_ERROR = "Permission Error"
"""Category for file system and resource permission failures."""

# Network and Connectivity Failures
NETWORK_ERROR = "Network Error"
"""Category for network-related failures (connection refused, DNS errors, etc.)."""

# Configuration and Environment Failures
CONFIG_ERROR = "Configuration Error"
"""Category for configuration and environment variable failures."""

# Data and Storage Failures
DB_ERROR = "Database Error"
"""Category for database connection and query failures."""

# Resource Exhaustion Failures
RESOURCE_ERROR = "Resource Error"
"""Category for resource exhaustion failures (memory, disk space, quotas, etc.)."""

# Catch-all Category
OTHER = "Other"
"""Category for errors that don't match any specific pattern or are unclassified."""