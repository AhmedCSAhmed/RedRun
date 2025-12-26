import io
from pathlib import Path
from typing import List

from redrun.ingest.normalizer import Normalizer
from redrun.ingest.sources.file import FileSource
from redrun.ingest.sources.stdin import StdinSource
from redrun.ingest.sources.source import Source


class MockSource:
    """Mock source for testing"""
    def __init__(self, lines: List[str]):
        self.lines = lines
    
    def read(self) -> List[str]:
        return self.lines


def test_normalizer_initialization_with_valid_source():
    """Test that Normalizer initializes correctly with a valid Source"""
    mock_source = MockSource(["test line"])
    normalizer = Normalizer(mock_source)
    assert normalizer.source == mock_source
    print("✓ Normalizer initialized with valid source")


def test_normalizer_initialization_with_invalid_source():
    """Test that Normalizer raises ValueError with invalid source"""
    try:
        normalizer = Normalizer("not a source")  # type: ignore
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "source must be an instance of Source" in str(e)
        print(f"✓ Normalizer correctly rejected invalid source: {e}")


def test_normalize_parses_valid_log_lines():
    """Test that normalize correctly parses log lines matching the pattern"""
    lines = [
        "[2024-01-15 10:30:45] ERROR: Database connection failed",
        "[2024-01-15 10:31:00] WARNING: High memory usage detected",
        "[2024-01-15 10:32:15] INFO: Request processed successfully"
    ]
    mock_source = MockSource(lines)
    normalizer = Normalizer(mock_source)
    
    result = normalizer.normalize()
    
    assert len(result) == 3
    assert result[0]["timestamp"] == "2024-01-15 10:30:45"
    assert result[0]["level"] == "ERROR"
    assert result[0]["message"] == "Database connection failed"
    
    assert result[1]["level"] == "WARNING"
    assert result[2]["level"] == "INFO"
    
    print("✓ Normalizer parsed valid log lines correctly")
    print(f"  Parsed {len(result)} lines: {result}")


def test_normalize_handles_unparsed_lines():
    """Test that normalize handles lines that don't match the pattern"""
    lines = [
        "[2024-01-15 10:30:45] ERROR: Valid log line",
        "This is just a plain text line",
        "Another unparsed line without brackets"
    ]
    mock_source = MockSource(lines)
    normalizer = Normalizer(mock_source)
    
    result = normalizer.normalize()
    
    assert len(result) == 3
    # First line should be parsed
    assert result[0]["timestamp"] == "2024-01-15 10:30:45"
    assert result[0]["level"] == "ERROR"
    
    # Other lines should be marked as UNPARSED
    assert result[1]["timestamp"] == "UNKNOWN"
    assert result[1]["level"] == "UNPARSED"
    assert result[1]["message"] == "This is just a plain text line"
    
    assert result[2]["level"] == "UNPARSED"
    
    print("✓ Normalizer handled unparsed lines correctly")
    print(f"  Result: {result}")


def test_normalize_with_empty_source():
    """Test that normalize handles empty source gracefully"""
    mock_source = MockSource([])
    normalizer = Normalizer(mock_source)
    
    result = normalizer.normalize()
    
    assert result == []
    print("✓ Normalizer handled empty source correctly")


def test_normalize_with_file_source(tmp_path):
    """Test normalizer integration with FileSource"""
    log_file: Path = tmp_path / "test.log"
    log_file.write_text(
        "[2024-01-15 10:30:45] ERROR: File error occurred\n"
        "[2024-01-15 10:31:00] INFO: File operation completed\n"
    )
    
    file_source = FileSource(log_file)
    normalizer = Normalizer(file_source)
    
    result = normalizer.normalize()
    
    assert len(result) == 2
    assert result[0]["level"] == "ERROR"
    assert result[1]["level"] == "INFO"
    
    print("✓ Normalizer works with FileSource")
    print(f"  Parsed {len(result)} lines from file")


def test_normalize_with_stdin_source(monkeypatch):
    """Test normalizer integration with StdinSource"""
    fake_stdin = io.StringIO(
        "[2024-01-15 10:30:45] ERROR: Stdin error\n"
        "[2024-01-15 10:31:00] WARNING: Stdin warning\n"
    )
    
    import redrun.ingest.sources.stdin as stdin_module
    monkeypatch.setattr(stdin_module, "sys", type("FakeSys", (), {"stdin": fake_stdin}))
    
    stdin_source = StdinSource()
    normalizer = Normalizer(stdin_source)
    
    result = normalizer.normalize()
    
    assert len(result) == 2
    assert result[0]["level"] == "ERROR"
    assert result[1]["level"] == "WARNING"
    
    print("✓ Normalizer works with StdinSource")
    print(f"  Parsed {len(result)} lines from stdin")


def test_normalize_with_mixed_content():
    """Test normalizer with mix of parsed and unparsed lines"""
    lines = [
        "[2024-01-15 10:30:45] ERROR: This is parsed",
        "This is not parsed",
        "[2024-01-15 10:31:00] INFO: This is also parsed",
        "Neither is this",
        "[2024-01-15 10:32:00] WARNING: Another parsed line"
    ]
    mock_source = MockSource(lines)
    normalizer = Normalizer(mock_source)
    
    result = normalizer.normalize()
    
    assert len(result) == 5
    # Check parsed lines
    assert result[0]["level"] == "ERROR"
    assert result[2]["level"] == "INFO"
    assert result[4]["level"] == "WARNING"
    
    # Check unparsed lines
    assert result[1]["level"] == "UNPARSED"
    assert result[3]["level"] == "UNPARSED"
    
    print("✓ Normalizer handled mixed content correctly")
    print(f"  Total lines: {len(result)}, Parsed: 3, Unparsed: 2")


def test_log_pattern_matches_various_formats():
    """Test that LOG_PATTERN matches various timestamp and level formats"""
    test_cases = [
        ("[2024-01-15 10:30:45] ERROR: Message", "2024-01-15 10:30:45", "ERROR"),
        ("[2024-12-31 23:59:59] WARNING: End of year", "2024-12-31 23:59:59", "WARNING"),
        ("[2024-01-01 00:00:00] INFO: New year", "2024-01-01 00:00:00", "INFO"),
        ("[2024-01-15] DEBUG: No time", "2024-01-15", "DEBUG"),
    ]
    
    for line, expected_timestamp, expected_level in test_cases:
        match = Normalizer.LOG_PATTERN.match(line)
        assert match is not None, f"Pattern should match: {line}"
        assert match.group("timestamp") == expected_timestamp
        assert match.group("level") == expected_level
    
    print("✓ LOG_PATTERN matches various formats correctly")


def test_normalize_handles_malformed_data():
    """Test that normalize attempts to match malformed log entries and handles them appropriately"""
    lines = [
        # Valid entry
        "[2024-01-15 10:30:45] ERROR: Valid log entry",
        
        # Malformed entries - missing parts (should try to match, fail, mark as UNPARSED)
        "[2024-01-15 10:30:45] ERROR",  # Missing colon and message
        "[2024-01-15 10:30:45]",  # Missing level and message
        "[2024-01-15 10:30:45] : Missing level",  # Missing level (empty level)
        "ERROR: Missing brackets",  # Missing brackets and timestamp
        "[2024-01-15 10:30:45 ERROR: Missing closing bracket",  # Missing closing bracket
        "2024-01-15 10:30:45] ERROR: Missing opening bracket",  # Missing opening bracket
        
        # Malformed entries - wrong format (should try to match, fail, mark as UNPARSED)
        "[2024-01-15 10:30:45 ERROR: No space before level",  # Missing space
        "[2024-01-15 10:30:45]ERROR: No space after bracket",  # Missing space
        "[2024-01-15 10:30:45] ERROR Missing colon",  # Missing colon
        "[2024-01-15 10:30:45] ERROR:: Double colon",  # Double colon (might match!)
        
        # Edge cases (should try to match, fail, mark as UNPARSED)
        "",  # Empty line
        "   ",  # Whitespace only
        "[",  # Just opening bracket
        "]",  # Just closing bracket
        "[]",  # Empty brackets
        "[] ERROR: Empty timestamp",  # Empty timestamp field
        "[2024-01-15 10:30:45] : Empty level",  # Empty level
        "[2024-01-15 10:30:45] ERROR:",  # Empty message (might match!)
        
        # Special characters that might break parsing (should still try to match)
        "[2024-01-15 10:30:45] ERROR: Message with [nested] brackets",  # Should match
        "[2024-01-15 10:30:45] ERROR: Message with : colons inside",  # Should match
        "[2024-01-15 10:30:45] ERROR: Message with\nnewlines",  # Should match
        "[2024-01-15 10:30:45] ERROR: Message with\t tabs",  # Should match
        
        # Very long line (should try to match)
        "[2024-01-15 10:30:45] ERROR: " + "x" * 1000,  # Very long message - should match
        
        # Unicode and special characters (should try to match)
        "[2024-01-15 10:30:45] ERROR: Message with émojis 🚀 and unicode",  # Should match
        "[2024-01-15 10:30:45] ERROR: Message with \"quotes\" and 'apostrophes'",  # Should match
    ]
    
    mock_source = MockSource(lines)
    normalizer = Normalizer(mock_source)
    
    result = normalizer.normalize()
    
    # Should process all lines without crashing
    assert len(result) == len(lines)
    
    # Show detailed matching results
    print("✓ Normalizer attempted to match all entries (including malformed)")
    print(f"  Total lines processed: {len(result)}")
    print("\n  Detailed matching results:")
    print("  " + "=" * 80)
    
    for i, (line, res) in enumerate(zip(lines, result)):
        # Check if pattern matched
        pattern_match = Normalizer.LOG_PATTERN.match(line)
        matched = "✓ MATCHED" if pattern_match else "✗ NO MATCH"
        
        # Show the result
        status = res["level"]
        if status == "UNPARSED":
            status_display = "UNPARSED (no pattern match)"
        elif status == "ERROR" and res.get("timestamp") == "ERROR PARSING LOG LINE":
            # This is an actual parsing error/exception, not a log level
            status_display = f"ERROR (parsing exception: {res.get('message', '')[:50]})"
        else:
            # This is a successfully parsed log entry with a log level
            msg_preview = res.get('message', '')[:40]
            if len(res.get('message', '')) > 40:
                msg_preview += "..."
            status_display = f"PARSED: level={status}, ts={res.get('timestamp', 'N/A')[:20]}, msg='{msg_preview}'"
        
        line_preview = line[:60] + "..." if len(line) > 60 else line
        print(f"  Line {i+1:2d}: {matched:12s} -> {status_display}")
        print(f"           '{line_preview}'")
        print()
    
    # Count results
    # Parsed = lines that matched pattern and were successfully parsed (have a real timestamp, not "UNKNOWN" or "ERROR PARSING LOG LINE")
    parsed_count = sum(1 for r in result if r.get("timestamp") not in ["UNKNOWN", "ERROR PARSING LOG LINE"])
    unparsed_count = sum(1 for r in result if r["level"] == "UNPARSED")
    # Error count = lines that caused exceptions during parsing
    error_count = sum(1 for r in result if r.get("timestamp") == "ERROR PARSING LOG LINE")
    
    print(f"  Summary: {parsed_count} parsed, {unparsed_count} unparsed, {error_count} errors")
    
    # Verify that the normalizer tried to match everything
    # Valid entries should be parsed
    assert result[0]["level"] == "ERROR", "First valid entry should be parsed"
    assert result[0]["timestamp"] == "2024-01-15 10:30:45"
    
    # Entries that match the pattern should be parsed (even if malformed in other ways)
    # Entries that don't match should be UNPARSED
    # Entries that cause exceptions should be ERROR
    
    # Verify some specific cases
    # Lines with proper format should match and be parsed
    assert result[0]["level"] == "ERROR", "First valid entry should be parsed as ERROR level"
    assert result[0]["timestamp"] == "2024-01-15 10:30:45"
    
    # Lines 20-25 (indices 20-25) have proper format and should match
    assert result[20]["level"] == "ERROR", "Message with nested brackets should match and parse"
    assert result[21]["level"] == "ERROR", "Message with colons inside should match and parse"
    assert result[22]["level"] == "ERROR", "Message with newlines should match and parse"
    assert result[23]["level"] == "ERROR", "Message with tabs should match and parse"
    assert result[24]["level"] == "ERROR", "Very long message should match and parse"
    assert result[25]["level"] == "ERROR", "Unicode message should match and parse"
    
    # Lines missing required parts should not match (be UNPARSED)
    assert result[1]["level"] == "UNPARSED", "Missing colon and message should not match"
    assert result[2]["level"] == "UNPARSED", "Missing level and message should not match"
    assert result[4]["level"] == "UNPARSED", "Missing brackets should not match"

