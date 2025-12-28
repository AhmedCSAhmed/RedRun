"""
RedRun - CI Failure Analysis Tool

RedRun is a command-line tool for analyzing CI build logs. It extracts
error information from raw build logs, classifies failures into actionable
categories, and produces concise summaries to help developers quickly
identify and fix CI failures.

The tool follows a pipeline architecture:
1. Ingest: Read log data from files or stdin
2. Normalize: Parse log lines into structured format
3. Extract: Filter for error-level events and stack traces
4. Classify: Categorize errors using pattern matching
5. Output: Display formatted results to console

Example usage:
    >>> from redrun.cli.main import run_analyze
    >>> run_analyze("build.log", summary_only=False)

Or from command line:
    $ redrun analyze build.log
    $ cat build.log | redrun analyze
    $ redrun analyze build.log --summary-only

Main Components:
    - redrun.ingest: Log reading and normalization
    - redrun.extract: Error extraction from normalized logs
    - redrun.classify: Error classification into categories
    - redrun.output: Console output formatting
    - redrun.cli: Command-line interface
"""

__version__ = "0.1.0"
__author__ = "RedRun Contributors"
__description__ = "CI failure analysis tool that parses build logs and extracts error information"
