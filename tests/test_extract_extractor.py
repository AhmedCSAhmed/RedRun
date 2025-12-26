from typing import List, Dict

from redrun.extract.extractor import Extractor


def test_extractor_initialization_with_default_errors():
    """Test that Extractor initializes with default error levels"""
    extractor = Extractor()
    assert extractor.errors == {"ERROR", "FATAL", "CRITICAL"}
    print("PASS: Extractor initialized with default error levels")


def test_extractor_initialization_with_custom_errors():
    """Test that Extractor accepts custom error levels"""
    extractor = Extractor(errors={"ERROR", "WARNING"})
    assert extractor.errors == {"ERROR", "WARNING"}
    print("PASS: Extractor initialized with custom error levels")


def test_extractor_case_insensitive_initialization():
    """Test that error levels are converted to uppercase"""
    extractor = Extractor(errors={"error", "Fatal", "critical"})
    assert extractor.errors == {"ERROR", "FATAL", "CRITICAL"}
    print("PASS: Extractor converts error levels to uppercase")


def test_extract_filters_error_levels():
    """Test that extract filters entries by error level"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "ERROR", "message": "Database connection failed", "line_number": "1"},
        {"timestamp": "2024-01-15 10:31:00", "level": "INFO", "message": "Request processed", "line_number": "2"},
        {"timestamp": "2024-01-15 10:32:00", "level": "FATAL", "message": "System crash", "line_number": "3"},
        {"timestamp": "2024-01-15 10:33:00", "level": "WARNING", "message": "High memory usage", "line_number": "4"},
        {"timestamp": "2024-01-15 10:34:00", "level": "CRITICAL", "message": "Service unavailable", "line_number": "5"},
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    stats = extractor.get_stats()
    
    assert len(results) == 3
    assert results[0]["level"] == "ERROR"
    assert results[1]["level"] == "FATAL"
    assert results[2]["level"] == "CRITICAL"
    
    # Verify stats match
    assert stats["total_lines"] == 5
    assert stats["extracted_count"] == 3
    assert stats["filtered_noise_count"] == 2  # INFO and WARNING
    
    print("PASS: Extractor correctly filters error levels")
    print(f"  Extracted {len(results)} errors from {len(log_entries)} entries")
    print(f"  Stats: {stats['filtered_noise_count']} lines of noise filtered")
    print("\n  Extracted errors:")
    for i, error in enumerate(results, 1):
        line_num = error.get('line_number', 'N/A')
        print(f"    {i}. Line {line_num} - [{error['level']}] {error['timestamp']}: {error['message']}")


def test_extract_case_insensitive_matching():
    """Test that extract matches error levels case-insensitively"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "error", "message": "Lowercase error"},
        {"timestamp": "2024-01-15 10:31:00", "level": "Error", "message": "Mixed case error"},
        {"timestamp": "2024-01-15 10:32:00", "level": "ERROR", "message": "Uppercase error"},
        {"timestamp": "2024-01-15 10:33:00", "level": "Fatal", "message": "Mixed case fatal"},
        {"timestamp": "2024-01-15 10:34:00", "level": "INFO", "message": "Info message"},
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    
    assert len(results) == 4
    assert all(result["level"].lower() in ["error", "fatal"] for result in results)
    
    print("PASS: Extractor handles case-insensitive matching")
    print(f"  Matched {len(results)} errors with various cases")


def test_extract_detects_stack_traces():
    """Test that extract detects and includes stack traces"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "INFO", "message": "Traceback (most recent call last):"},
        {"timestamp": "2024-01-15 10:31:00", "level": "DEBUG", "message": "  File \"/app/test.py\", line 42"},
        {"timestamp": "2024-01-15 10:32:00", "level": "INFO", "message": "    user = UserService.create()"},
        {"timestamp": "2024-01-15 10:33:00", "level": "INFO", "message": "AttributeError: module has no attribute"},
        {"timestamp": "2024-01-15 10:34:00", "level": "INFO", "message": "Normal log message"},
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    
    # Should extract stack trace entries even though they're INFO level
    assert len(results) >= 2  # At least the stack trace entries (Traceback and File)
    assert any("Traceback" in result["message"] for result in results)
    assert any("File \"" in result["message"] for result in results)
    
    print("PASS: Extractor detects stack traces")
    print(f"  Extracted {len(results)} entries with stack traces")


def test_extract_with_mixed_content():
    """Test extract with mix of errors, stack traces, and normal logs"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "ERROR", "message": "Database error", "line_number": "1"},
        {"timestamp": "2024-01-15 10:31:00", "level": "INFO", "message": "Normal operation", "line_number": "2"},
        {"timestamp": "2024-01-15 10:32:00", "level": "WARNING", "message": "High memory", "line_number": "3"},
        {"timestamp": "2024-01-15 10:33:00", "level": "INFO", "message": "Traceback (most recent call last):", "line_number": "4"},
        {"timestamp": "2024-01-15 10:34:00", "level": "CRITICAL", "message": "System failure", "line_number": "5"},
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    
    assert len(results) == 3  # ERROR, stack trace, CRITICAL
    assert results[0]["level"] == "ERROR"
    assert "Traceback" in results[1]["message"]
    assert results[2]["level"] == "CRITICAL"
    
    print("PASS: Extractor handles mixed content correctly")
    print(f"  Extracted {len(results)} errors/stack traces from {len(log_entries)} entries")
    print("\n  Extracted errors:")
    for i, error in enumerate(results, 1):
        print(f"    {i}. [{error['level']}] {error['message'][:60]}...")


def test_extract_with_empty_input():
    """Test that extract handles empty input gracefully"""
    extractor = Extractor()
    results = list(extractor.extract([]))
    
    assert results == []
    print("PASS: Extractor handles empty input correctly")


def test_extract_with_missing_keys():
    """Test that extract handles entries with missing keys gracefully"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "ERROR", "message": "Valid error"},
        {"timestamp": "2024-01-15 10:31:00", "message": "Missing level key"},
        {"level": "ERROR", "message": "Missing timestamp"},  # Still valid - has level
        {},  # Empty dict - will be skipped
        {"timestamp": "2024-01-15 10:34:00", "level": "FATAL", "message": "Valid fatal"},
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    
    # Should extract entries with valid level (even if timestamp is missing)
    # and skip entries without level key
    assert len(results) == 3  # ERROR, ERROR (missing timestamp), FATAL
    assert results[0]["level"] == "ERROR"
    assert results[1]["level"] == "ERROR"  # Missing timestamp but has level
    assert results[2]["level"] == "FATAL"
    
    print("PASS: Extractor handles missing keys gracefully")
    print(f"  Extracted {len(results)} valid entries, skipped entries without level key")


def test_extract_with_custom_error_levels():
    """Test extract with custom error level set"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "ERROR", "message": "Error message"},
        {"timestamp": "2024-01-15 10:31:00", "level": "WARNING", "message": "Warning message"},
        {"timestamp": "2024-01-15 10:32:00", "level": "INFO", "message": "Info message"},
    ]
    
    extractor = Extractor(errors={"WARNING"})
    results = list(extractor.extract(log_entries))
    
    assert len(results) == 1
    assert results[0]["level"] == "WARNING"
    
    print("PASS: Extractor works with custom error levels")
    print(f"  Extracted {len(results)} entries matching custom levels")


def test_is_stack_trace_detection():
    """Test stack trace detection with various patterns"""
    extractor = Extractor()
    
    test_cases = [
        ("Traceback (most recent call last):", True),
        ("Traceback", True),
        ('  File "/app/test.py", line 42', True),
        ('File "/app/test.py"', True),
        ("at 0x7f8b1c000000", True),
        ("Error at /path/to/file.py", True),
        ("Error at C:\\path\\to\\file.py", True),
        ("Normal log message", False),
        ("Error occurred", False),
        ("", False),
    ]
    
    for message, expected in test_cases:
        result = extractor._is_stack_trace(message)
        assert result == expected, f"Expected {expected} for message: {message[:50]}"
    
    print("PASS: Stack trace detection works correctly")
    print(f"  Tested {len(test_cases)} different patterns")


def test_extract_preserves_all_fields():
    """Test that extract preserves all fields from log entries"""
    log_entries = [
        {
            "timestamp": "2024-01-15 10:30:45",
            "level": "ERROR",
            "message": "Database connection failed",
            "extra_field": "extra_value"
        }
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    
    assert len(results) == 1
    assert results[0]["timestamp"] == "2024-01-15 10:30:45"
    assert results[0]["level"] == "ERROR"
    assert results[0]["message"] == "Database connection failed"
    assert results[0]["extra_field"] == "extra_value"
    
    print("PASS: Extractor preserves all fields from log entries")


def test_extract_tracks_filtered_noise():
    """Test that extract tracks filtered noise count correctly"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "ERROR", "message": "Error message", "line_number": "1"},
        {"timestamp": "2024-01-15 10:31:00", "level": "INFO", "message": "Info message", "line_number": "2"},
        {"timestamp": "2024-01-15 10:32:00", "level": "WARNING", "message": "Warning message", "line_number": "3"},
        {"timestamp": "2024-01-15 10:33:00", "level": "FATAL", "message": "Fatal message", "line_number": "4"},
        {"timestamp": "2024-01-15 10:34:00", "level": "DEBUG", "message": "Debug message", "line_number": "5"},
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    stats = extractor.get_stats()
    
    assert stats["total_lines"] == 5
    assert stats["extracted_count"] == 2  # ERROR and FATAL
    assert stats["filtered_noise_count"] == 3  # INFO, WARNING, DEBUG
    assert len(results) == stats["extracted_count"]
    
    print("PASS: Extractor tracks filtered noise correctly")
    print(f"  Total: {stats['total_lines']}, Extracted: {stats['extracted_count']}, Filtered: {stats['filtered_noise_count']}")
    print("\n  Extracted errors:")
    for i, error in enumerate(results, 1):
        print(f"    {i}. [{error['level']}] {error['message']}")


def test_extract_stats_with_empty_input():
    """Test stats with empty input"""
    extractor = Extractor()
    results = list(extractor.extract([]))
    stats = extractor.get_stats()
    
    assert stats["total_lines"] == 0
    assert stats["extracted_count"] == 0
    assert stats["filtered_noise_count"] == 0
    assert len(results) == 0
    
    print("PASS: Stats work correctly with empty input")


def test_extract_stats_with_mixed_content():
    """Test stats with mix of errors, stack traces, and normal logs"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "ERROR", "message": "Database error"},
        {"timestamp": "2024-01-15 10:31:00", "level": "INFO", "message": "Normal operation"},
        {"timestamp": "2024-01-15 10:32:00", "level": "WARNING", "message": "High memory"},
        {"timestamp": "2024-01-15 10:33:00", "level": "INFO", "message": "Traceback (most recent call last):"},
        {"timestamp": "2024-01-15 10:34:00", "level": "CRITICAL", "message": "System failure"},
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    stats = extractor.get_stats()
    
    assert stats["total_lines"] == 5
    assert stats["extracted_count"] == 3  # ERROR, stack trace, CRITICAL
    assert stats["filtered_noise_count"] == 2  # INFO (normal), WARNING
    assert len(results) == stats["extracted_count"]
    
    print("PASS: Stats work correctly with mixed content")
    print(f"  Extracted {stats['extracted_count']} errors, filtered {stats['filtered_noise_count']} noise lines")


def test_extract_stats_reset_on_new_extraction():
    """Test that stats reset when extract is called again"""
    log_entries_1 = [
        {"timestamp": "2024-01-15 10:30:45", "level": "ERROR", "message": "Error 1"},
        {"timestamp": "2024-01-15 10:31:00", "level": "INFO", "message": "Info 1"},
    ]
    
    log_entries_2 = [
        {"timestamp": "2024-01-15 10:32:00", "level": "FATAL", "message": "Fatal 1"},
        {"timestamp": "2024-01-15 10:33:00", "level": "INFO", "message": "Info 2"},
        {"timestamp": "2024-01-15 10:34:00", "level": "DEBUG", "message": "Debug 1"},
    ]
    
    extractor = Extractor()
    
    # First extraction
    results1 = list(extractor.extract(log_entries_1))
    stats1 = extractor.get_stats()
    assert stats1["total_lines"] == 2
    assert stats1["extracted_count"] == 1
    assert stats1["filtered_noise_count"] == 1
    
    # Second extraction (should reset)
    results2 = list(extractor.extract(log_entries_2))
    stats2 = extractor.get_stats()
    assert stats2["total_lines"] == 3
    assert stats2["extracted_count"] == 1
    assert stats2["filtered_noise_count"] == 2
    
    # Stats should reflect second extraction, not cumulative
    assert stats2["total_lines"] != stats1["total_lines"]
    
    print("PASS: Stats reset correctly on new extraction")
    print(f"  First: {stats1['total_lines']} lines, Second: {stats2['total_lines']} lines")


def test_extract_stats_with_missing_keys():
    """Test stats count entries with missing keys as filtered noise"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "ERROR", "message": "Valid error"},
        {"timestamp": "2024-01-15 10:31:00", "message": "Missing level key"},
        {},  # Empty dict
        {"timestamp": "2024-01-15 10:34:00", "level": "FATAL", "message": "Valid fatal"},
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    stats = extractor.get_stats()
    
    assert stats["total_lines"] == 4
    assert stats["extracted_count"] == 2  # ERROR and FATAL
    assert stats["filtered_noise_count"] == 2  # Missing level key and empty dict
    assert len(results) == stats["extracted_count"]
    
    print("PASS: Stats correctly count missing keys as filtered noise")
    print(f"  Extracted {stats['extracted_count']}, Filtered {stats['filtered_noise_count']} (including invalid entries)")


def test_extract_stats_with_all_errors():
    """Test stats when all entries are errors"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "ERROR", "message": "Error 1"},
        {"timestamp": "2024-01-15 10:31:00", "level": "FATAL", "message": "Fatal 1"},
        {"timestamp": "2024-01-15 10:32:00", "level": "CRITICAL", "message": "Critical 1"},
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    stats = extractor.get_stats()
    
    assert stats["total_lines"] == 3
    assert stats["extracted_count"] == 3
    assert stats["filtered_noise_count"] == 0
    assert len(results) == 3
    
    print("PASS: Stats work correctly when all entries are errors")
    print(f"  No noise filtered: {stats['filtered_noise_count']} filtered, {stats['extracted_count']} extracted")


def test_extract_stats_with_all_noise():
    """Test stats when all entries are noise (non-errors)"""
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "INFO", "message": "Info 1"},
        {"timestamp": "2024-01-15 10:31:00", "level": "WARNING", "message": "Warning 1"},
        {"timestamp": "2024-01-15 10:32:00", "level": "DEBUG", "message": "Debug 1"},
    ]
    
    extractor = Extractor()
    results = list(extractor.extract(log_entries))
    stats = extractor.get_stats()
    
    assert stats["total_lines"] == 3
    assert stats["extracted_count"] == 0
    assert stats["filtered_noise_count"] == 3
    assert len(results) == 0
    
    print("PASS: Stats work correctly when all entries are noise")
    print(f"  All filtered: {stats['filtered_noise_count']} noise, {stats['extracted_count']} extracted")



