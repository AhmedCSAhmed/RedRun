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

### Development Installation (Editable Mode)

To install RedRun in development mode so you can use it and make changes:

```bash
# Clone or navigate to the RedRun directory
cd RedRun

# Create a virtual environment (if you haven't already)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .
```

After installation, you can use RedRun from anywhere (as long as your virtual environment is activated):

```bash
# Activate your virtual environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Then use redrun
redrun analyze build.log
```

**Note**: If the `redrun` command doesn't work, you can always use:

```bash
python -m redrun.cli.main analyze build.log
```

## Usage

### Basic Usage

```bash
# Analyze a log file
redrun analyze build.log

# Read from stdin (pipe input)
cat build.log | redrun analyze

# Summary only (quick overview)
redrun analyze build.log --summary-only
```

### Example Output

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
