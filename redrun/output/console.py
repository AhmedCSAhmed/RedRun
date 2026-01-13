"""
Console output formatting module.

This module provides the Console class which formats classified errors
for display in the terminal. It creates user-friendly output including:
- ASCII art logo header
- Summary statistics (total lines, errors extracted, noise filtered)
- Category breakdown with counts
- Detailed error listings with line numbers, levels, categories, and confidence scores

The output is designed to be readable and actionable, helping developers
quickly identify the most important errors in CI build logs.
"""

from typing import List, Dict
from collections import Counter
import sys


class Console:
    """
    Formats classified errors for console output.
    
    Takes classified error entries and formats them into a readable
    console display with category summaries and detailed error listings.
    """
    
    def __init__(self, output_stream=sys.stdout):
        """
        Initialize console formatter.
        
        Args:
            output_stream: Where to write output (default: sys.stdout)
        """
        self.output = output_stream
    
    def display(self, classified_errors: List[Dict[str, str]], extract_stats: Dict[str, int] = None) -> None:
        """
        Display classified errors in a formatted console output.
        
        Args:
            classified_errors: List of classified error dictionaries from Classifier
            extract_stats: Optional extraction statistics from Extractor
        """
        # Display REDRUN logo
        self._display_logo()
        
        if not classified_errors:
            self._write("No errors found in log file.\n")
            return
        
        # Count categories
        category_counts = Counter([error['category'] for error in classified_errors])
        
        # Display summary
        self._display_summary(category_counts, extract_stats)
        
        # Display detailed errors
        self._display_errors(classified_errors)
    
    def _display_summary(self, category_counts: Counter, extract_stats: Dict[str, int] = None) -> None:
        """
        Display failure summary with category counts and extraction statistics.
        
        Formats and displays a summary section including:
        - Total log lines processed
        - Number of errors extracted
        - Number of lines filtered as noise
        - Category breakdown with counts (sorted by frequency)
        
        Args:
            category_counts: Counter object mapping category names to error counts.
                           Categories are sorted by count (most common first).
            extract_stats: Optional dictionary with extraction statistics:
                          - total_lines: Total log lines processed
                          - extracted_count: Number of errors extracted
                          - filtered_noise_count: Number of lines filtered out
        """
        self._write("\n")
        self._write("=" * 80 + "\n")
        self._write("FAILURE SUMMARY\n")
        self._write("=" * 80 + "\n")
        
        if extract_stats:
            self._write(f"Total log lines: {extract_stats.get('total_lines', 0)}\n")
            self._write(f"Errors extracted: {extract_stats.get('extracted_count', 0)}\n")
            self._write(f"Noise filtered: {extract_stats.get('filtered_noise_count', 0)}\n")
            self._write("\n")
        
        if category_counts:
            self._write("Category Breakdown:\n")
            self._write("-" * 80 + "\n")
            for category, count in category_counts.most_common():
                self._write(f"  {category:30} : {count}\n")
        
        self._write("\n")
    
    def _display_errors(self, classified_errors: List[Dict[str, str]]) -> None:
        """
        Display detailed error listings with full information.
        
        Formats and displays each classified error with:
        - Sequential number
        - Line number from original log
        - Log level (ERROR, FATAL, etc.)
        - Category classification
        - Confidence score as percentage
        - Message preview (truncated to 100 characters if longer)
        
        Args:
            classified_errors: List of classified error dictionaries, each containing:
                              - line_number: Line number from original log
                              - level: Log level string
                              - category: Category classification
                              - confidence: Confidence score (0.0-1.0)
                              - message: Original error message
        """
        self._write("=" * 80 + "\n")
        self._write("DETAILED ERRORS\n")
        self._write("=" * 80 + "\n")
        
        for i, error in enumerate(classified_errors, 1):
            line_num = error.get('line_number', 'N/A')
            level = error.get('level', 'N/A')
            category = error.get('category', 'N/A')
            confidence = error.get('confidence', 0.0)
            message = error.get('message', '')
            
            # Format confidence as percentage
            confidence_pct = f"{confidence * 100:.0f}%"
            
            # Display message with proper formatting
            # For multi-line messages (from UNPARSED binding), show first 2-3 lines
            # For single-line messages, show up to 400 characters
            message_lines = message.split('\n')
            if len(message_lines) > 1:
                # Multi-line message: show first 3 lines or first 400 chars total
                preview_lines = []
                total_chars = 0
                for line in message_lines[:3]:
                    if total_chars + len(line) <= 400:
                        preview_lines.append(line)
                        total_chars += len(line) + 1  # +1 for newline
                    else:
                        # Truncate this line if needed
                        remaining = 400 - total_chars
                        if remaining > 20:  # Only add if meaningful space left
                            preview_lines.append(line[:remaining] + "...")
                        break
                msg_preview = '\n   '.join(preview_lines)
                if len(message_lines) > 3 or total_chars >= 400:
                    msg_preview += "\n   ..."
            else:
                # Single-line message: show up to 400 characters
                msg_preview = message[:400] + "..." if len(message) > 400 else message
            
            self._write(f"\n{i}. Line {line_num:4} | [{level:8}] | {category:25} | Confidence: {confidence_pct:>4}\n")
            self._write(f"   {msg_preview}\n")
        
        self._write("\n")
    
    def _display_logo(self) -> None:
        """
        Display REDRUN ASCII art logo header.
        
        Creates a visually distinctive header using block characters (█)
        to display the "REDRUN" name. The logo is centered within a
        bordered box for better visual separation from the rest of the output.
        """
        self._write("\n")
        self._write("=" * 80 + "\n")
        self._write("\n")
        self._write("  " + "█" * 76 + "\n")
        self._write("  " + "█" + " " * 74 + "█" + "\n")
        self._write("  " + "█" + " " * 30 + "REDRUN" + " " * 30 + "█" + "\n")
        self._write("  " + "█" + " " * 74 + "█" + "\n")
        self._write("  " + "█" * 76 + "\n")
        self._write("\n")
        self._write("=" * 80 + "\n")
        self._write("\n")
    
    def _write(self, text: str) -> None:
        """
        Write text to the configured output stream.
        
        This is a convenience method that writes text to self.output
        (typically sys.stdout). It's used internally by all display
        methods to ensure consistent output handling.
        
        Args:
            text: String to write to the output stream. Should include
                 newline characters if line breaks are desired.
        """
        self.output.write(text)
    
    def display_summary_only(self, classified_errors: List[Dict[str, str]], extract_stats: Dict[str, int] = None) -> None:
        """
        Display only the summary (category counts) without detailed errors.
        
        Useful for quick overview.
        
        Args:
            classified_errors: List of classified error dictionaries from Classifier
            extract_stats: Optional extraction statistics from Extractor
        """
        # Display REDRUN logo
        self._display_logo()
        
        if not classified_errors:
            self._write("No errors found in log file.\n")
            return
        
        # Count categories
        category_counts = Counter([error['category'] for error in classified_errors])
        
        # Display summary
        self._display_summary(category_counts, extract_stats)

