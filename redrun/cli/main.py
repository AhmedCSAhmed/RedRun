#!/usr/bin/env python3
"""
RedRun CLI entrypoint.

This module provides the command-line interface for RedRun. It orchestrates
the entire pipeline:
1. Reading log data from files or stdin
2. Normalizing log lines into structured format
3. Extracting error-level events and stack traces
4. Classifying errors into actionable categories
5. Displaying formatted results to the console

The CLI supports:
- File input: `redrun analyze build.log`
- Stdin input: `cat build.log | redrun analyze`
- Summary-only mode: `redrun analyze build.log --summary-only`

This module also handles the editable install finder loading to ensure
the 'redrun' command works correctly in development environments.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional

def _ensure_editable_finder():
    """
    Load the editable finder if this is a development install.
    
    This function ensures that the editable finder module is loaded before
    importing redrun modules. This is necessary for editable installs
    (pip install -e) where the finder must be initialized before the
    package can be imported.
    
    The function searches for __editable__..._finder.py in site-packages
    and loads it if found. If no finder is found or an error occurs,
    the function silently returns, allowing normal import behavior.
    
    Note:
        This is a workaround for a known issue with editable installs
        where entry point scripts execute before .pth files are processed.
    """
    try:
        import site
        import importlib.util
        
        site_packages = [p for p in sys.path if 'site-packages' in p]
        if not site_packages:
            return
        
        site.addsitedir(site_packages[0])
        
        for sp in site_packages:
            try:
                for file in os.listdir(sp):
                    if file.startswith('__editable__') and file.endswith('_finder.py'):
                        finder_path = os.path.join(sp, file)
                        if os.path.exists(finder_path):
                            spec = importlib.util.spec_from_file_location("_editable_finder", finder_path)
                            if spec and spec.loader:
                                finder_module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(finder_module)
                                if hasattr(finder_module, 'install'):
                                    finder_module.install()
                                    return
            except (OSError, PermissionError):
                continue
    except Exception:
        pass

_ensure_editable_finder()

from redrun.ingest.reader import Reader
from redrun.ingest.normalizer import Normalizer
from redrun.extract.extractor import Extractor
from redrun.classify.classifier import Classifier
from redrun.output.console import Console


def main() -> int:
    """
    Main CLI entrypoint for the RedRun command.
    
    Parses command-line arguments and delegates to the appropriate command
    handler. Currently supports the 'analyze' command for analyzing log files.
    
    The function sets up argument parsing with:
    - 'analyze' subcommand for log analysis
    - Optional file path argument
    - --summary-only flag for summary-only output
    
    Returns:
        Exit code:
            - 0: Success
            - 1: Error (invalid arguments, command execution failure)
    
    Example:
        >>> # From command line:
        >>> # $ redrun analyze build.log
        >>> # $ redrun analyze build.log --summary-only
        >>> # $ cat build.log | redrun analyze
    """
    parser = argparse.ArgumentParser(
        prog='redrun',
        description='RedRun - CI failure analysis tool that parses build logs and extracts error information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  redrun analyze build.log
  cat build.log | redrun analyze
  redrun analyze build.log --summary-only

Built by Ahmed Ahmed (MVP)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze a log file or read from stdin'
    )
    analyze_parser.add_argument(
        'file',
        nargs='?',
        type=str,
        help='Path to log file (optional, reads from stdin if not provided)'
    )
    analyze_parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Display only the summary, not detailed errors'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'analyze':
        return run_analyze(args.file, args.summary_only)
    
    return 1


def run_analyze(file_path: Optional[str], summary_only: bool = False) -> int:
    """
    Run the analyze command on a log file or stdin.
    
    This function orchestrates the entire RedRun pipeline:
    1. Creates a Reader from file or stdin
    2. Normalizes log lines into structured format
    3. Extracts error-level events and stack traces
    4. Classifies errors into categories with confidence scores
    5. Displays results to console (full or summary-only)
    
    Args:
        file_path: Optional path to log file. If None, reads from stdin.
                  Relative paths are resolved to absolute paths.
                  If provided, must be a valid file path.
        summary_only: If True, only display summary statistics and category
                     breakdown without detailed error listings. If False,
                     display full output including all error details.
    
    Returns:
        Exit code:
            - 0: Success
            - 1: Error (file not found, invalid input, etc.)
            - 130: Interrupted by user (Ctrl+C)
    
    Raises:
        FileNotFoundError: If file_path is provided but file doesn't exist.
        PermissionError: If file_path cannot be read due to permissions.
        ValueError: If file_path points to a directory, not a file.
        IOError: For other I/O errors during reading.
    
    Example:
        >>> from redrun.cli.main import run_analyze
        >>> exit_code = run_analyze("build.log", summary_only=False)
        >>> # Or from stdin:
        >>> exit_code = run_analyze(None, summary_only=True)
    """
    try:
        if file_path:
            log_path = Path(file_path)
            if not log_path.is_absolute():
                log_path = log_path.resolve()
            
            if not log_path.exists():
                print(f"Error: File not found: {file_path}", file=sys.stderr)
                return 1
            if not log_path.is_file():
                print(f"Error: Not a file: {file_path}", file=sys.stderr)
                return 1
            reader = Reader.from_file(log_path)
        else:
            if sys.stdin.isatty():
                print("Error: No file provided and stdin is empty. Provide a file path or pipe input.", file=sys.stderr)
                return 1
            reader = Reader.from_stdin()
        
        normalizer = Normalizer(reader.source)
        normalized = normalizer.normalize()
        
        extractor = Extractor()
        errors = list(extractor.extract(normalized))
        extract_stats = extractor.get_stats()
        
        classifier = Classifier()
        classified = classifier.classify_batch(errors)
        
        console = Console()
        if summary_only:
            console.display_summary_only(classified, extract_stats)
        else:
            console.display(classified, extract_stats)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

