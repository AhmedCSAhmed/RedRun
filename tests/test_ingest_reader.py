import io
from pathlib import Path

from redrun.ingest.reader import Reader
from redrun.ingest.sources.file import FileSource
from redrun.ingest.sources.stdin import StdinSource


def test_file_source_reads_lines_and_strips_newlines(tmp_path):
    log_file: Path = tmp_path / "sample.log"
    log_file.write_text("first line\nsecond line\nthird line\n")

    source = FileSource(log_file)
    lines = source.read()
    print("file_source (Path) lines:", lines)

    assert lines == ["first line", "second line", "third line"]


def test_file_source_accepts_string_path(tmp_path):
    log_file: Path = tmp_path / "sample.log"
    log_file.write_text("only line\n")

    # Pass a str path even though the type annotation is Path
    source = FileSource(str(log_file))
    lines = source.read()
    print("file_source (str) lines:", lines)

    assert lines == ["only line"]


def test_stdin_source_reads_from_given_stream(monkeypatch):
    fake_stdin = io.StringIO("line 1\nline 2\n")

    # Monkeypatch sys.stdin used inside StdinSource
    import redrun.ingest.sources.stdin as stdin_module

    monkeypatch.setattr(stdin_module, "sys", type("FakeSys", (), {"stdin": fake_stdin}))

    source = StdinSource()
    lines = source.read()
    print("stdin_source lines:", lines)

    assert lines == ["line 1", "line 2"]


def test_reader_read_delegates_to_source():
    class FakeSource:
        def __init__(self):
            self.read_called = False

        def read(self):
            self.read_called = True
            return ["a", "b"]

    fake_source = FakeSource()
    reader = Reader(fake_source)

    result = reader.read()
    print("reader with FakeSource result:", result)

    assert fake_source.read_called is True
    assert result == ["a", "b"]


def test_reader_from_file_uses_file_source(tmp_path):
    log_file: Path = tmp_path / "sample.log"
    log_file.write_text("hello\nworld\n")

    reader = Reader.from_file(log_file)
    lines = reader.read()
    print("Reader.from_file lines:", lines)

    assert lines == ["hello", "world"]


def test_reader_from_stdin_uses_stdin_source(monkeypatch):
    fake_stdin = io.StringIO("alpha\nbeta\n")

    import redrun.ingest.sources.stdin as stdin_module

    monkeypatch.setattr(stdin_module, "sys", type("FakeSys", (), {"stdin": fake_stdin}))

    reader = Reader.from_stdin()
    lines = reader.read()
    print("Reader.from_stdin lines:", lines)

    assert lines == ["alpha", "beta"]


