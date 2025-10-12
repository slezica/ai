import pytest
from pathlib import Path
from ai import main


def test_fs_read_entire_file(sample_file):
    """fs_read returns entire file contents by default."""
    result = main.fs_read(str(sample_file))

    expected = sample_file.read_text()
    assert result == expected


def test_fs_read_with_start(sample_file):
    """fs_read reads from start line onwards."""
    result = main.fs_read(str(sample_file), start=2)

    lines = sample_file.read_text().splitlines(keepends=True)
    expected = "".join(lines[2:])
    assert result == expected


def test_fs_read_with_start_and_end(sample_file):
    """fs_read reads specified line range."""
    result = main.fs_read(str(sample_file), start=1, end=3)

    lines = sample_file.read_text().splitlines(keepends=True)
    expected = "".join(lines[1:4])
    assert result == expected


def test_fs_read_negative_end(sample_file):
    """fs_read handles negative end index."""
    result = main.fs_read(str(sample_file), start=0, end=-2)

    lines = sample_file.read_text().splitlines(keepends=True)
    expected = "".join(lines[0:len(lines) - 1])
    assert result == expected


def test_fs_read_single_line(sample_file):
    """fs_read can read a single line."""
    result = main.fs_read(str(sample_file), start=0, end=0)

    lines = sample_file.read_text().splitlines(keepends=True)
    expected = lines[0]
    assert result == expected


def test_fs_read_nonexistent(tmp_wd):
    """fs_read returns error for nonexistent file."""
    nonexistent = tmp_wd / "does_not_exist.txt"

    result = main.fs_read(str(nonexistent))

    assert result.startswith("Error:")
    assert "does not exist" in result


def test_fs_read_directory(sample_dir):
    """fs_read returns error when path is a directory."""
    result = main.fs_read(str(sample_dir))

    assert result.startswith("Error:")
    assert "not a file" in result


def test_fs_read_outside_wd(tmp_path):
    """fs_read returns error for paths outside working directory."""
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("content")

    result = main.fs_read(str(outside_file))

    assert result.startswith("Error:")
    assert "outside working directory" in result

def test_fs_read_relative(tmp_wd, sample_file):
    """fs_read takes paths relative to the working directory."""
    result1 = main.fs_read(sample_file)
    result2 = main.fs_read(Path(sample_file).name)

    assert result1 == result2
