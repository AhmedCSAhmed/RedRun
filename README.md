# RedRun

RedRun is a deterministic CI failure analysis tool that parses raw build logs from failed CI runs and extracts high-signal error information. It classifies failures into clear, actionable categories such as test failures, dependency issues, and infrastructure timeouts, reducing the need to manually sift through noisy CI output. RedRun is designed as a lightweight DevEx tool that prioritizes predictability, explainability, and fast feedback.

## Motivation

Modern CI systems surface large volumes of log output but provide little structure when builds fail. Developers often spend significant time identifying the root cause of failures and distinguishing primary errors from secondary noise. RedRun focuses on surfacing signal over noise by automatically identifying and categorizing common CI failure modes.

## Features (MVP)

- Parses raw CI log output from failed runs
- Extracts error signals and stack traces
- Classifies failures using deterministic, rule-based logic
- Groups failures into actionable categories
- Produces concise CLI summaries for fast debugging

## Design Principles

- Deterministic by default; no machine learning in the critical path
- Explainable output; every classification is traceable to a rule
- Low noise; prioritizes root causes over raw logs
- Extensible architecture for future enhancements

## Installation

### Easiest Method: Install from GitHub

Install RedRun directly from GitHub with one command:

```bash
pip install git+https://github.com/<username>/RedRun.git
```

Replace `<username>` with the actual GitHub username or organization name.

### Alternative: Install from Source

If you prefer to clone the repository first:

```bash
# Step 1: Clone the repository
git clone https://github.com/<username>/RedRun.git
cd RedRun

# Step 2: Install RedRun
pip install -e .
```

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- git (for cloning the repository)

## Usage

### Basic Commands

```bash
# Analyze a log file
redrun analyze build.log

# Read from stdin (pipe input from other commands)
cat build.log | redrun analyze

# Get a quick summary without detailed error listings
redrun analyze build.log --summary-only

# Show help
redrun --help
```

### Common Use Cases

**Analyze CI Build Logs:**

```bash
# Analyze a downloaded build log
redrun analyze build.log

# Pipe from curl/wget
curl https://your-ci-system.com/builds/123/logs | redrun analyze
```

**Analyze Application Logs:**

```bash
# Analyze application error logs
redrun analyze app.log

# Filter for specific time periods
tail -n 1000 app.log | redrun analyze
```

**Real-time Log Monitoring:**

```bash
# Monitor logs in real-time
tail -f app.log | redrun analyze
```

### Output Interpretation

RedRun categorizes errors into the following types:

- **Test Failure**: Unit tests, integration tests, or test suites that failed
- **Dependency Error**: Package resolution, missing dependencies, version conflicts
- **Infrastructure Timeout**: Network timeouts, operation timeouts, time limits exceeded
- **Build Error**: Compilation errors, syntax errors, type errors, build failures
- **Lint Error**: Code style violations, linting failures
- **Authentication Error**: Authentication failures, invalid credentials, expired tokens
- **Network Error**: Connection issues, DNS failures, network unreachable
- **Configuration Error**: Missing configuration, invalid settings, environment variables
- **Database Error**: Database connection failures, query timeouts, SQL errors
- **Permission Error**: File system permissions, access denied errors
- **Resource Error**: Out of memory, disk full, quota exceeded
- **Other**: Unclassified errors or errors that don't match specific patterns

Each error includes:

- **Line Number**: Where the error occurred in the original log
- **Log Level**: ERROR, FATAL, CRITICAL, etc.
- **Category**: The classification category
- **Confidence**: How confident RedRun is in the classification (0-100%)
- **Message Preview**: A preview of the error message

## Example Output

```
================================================================================

  ████████████████████████████████████████████████████████████████████████████
  █                                                                          █
  █                              REDRUN                              █
  █                                                                          █
  ████████████████████████████████████████████████████████████████████████████

================================================================================

================================================================================
FAILURE SUMMARY
================================================================================
Total log lines: 166
Errors extracted: 8
Noise filtered: 158

Category Breakdown:
--------------------------------------------------------------------------------
  Build Error                    : 4
  Test Failure                   : 1
  Database Error                 : 1
  Network Error                  : 1
  Configuration Error            : 1

================================================================================
DETAILED ERRORS
================================================================================
...
```

## Project Structure

```
redrun/
├── cli/          # CLI entrypoint
├── ingest/       # log ingestion and normalization
├── extract/      # error extraction
├── classify/     # rule-based failure classification
└── output/       # CLI output formatting
```

## Credits

Built by Ahmed Ahmed (MVP)
