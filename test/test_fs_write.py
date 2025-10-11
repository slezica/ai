import pytest
from pathlib import Path
from ai import main


def test_fs_write_new_file(tmp_wd):
    """fs_write creates a new file with content."""
    target = tmp_wd / "new_file.txt"
    content = "Hello, world!"

    result = main.fs_write(str(target), content)

    assert target.exists()
    assert target.read_text() == content
    assert "Successfully wrote 13 characters" in result
    assert "mode: w" in result


def test_fs_write_overwrite(tmp_wd):
    """fs_write overwrites existing file by default."""
    target = tmp_wd / "existing.txt"
    target.write_text("old content")

    new_content = "new content"
    result = main.fs_write(str(target), new_content)

    assert target.read_text() == new_content
    assert "Successfully wrote 11 characters" in result


def test_fs_write_append_mode(tmp_wd):
    """fs_write appends when mode is 'a'."""
    target = tmp_wd / "append.txt"
    target.write_text("first line\n")

    additional = "second line\n"
    result = main.fs_write(str(target), additional, mode='a')

    expected = "first line\nsecond line\n"
    assert target.read_text() == expected
    assert "mode: a" in result


def test_fs_write_empty_content(tmp_wd):
    """fs_write can write empty content."""
    target = tmp_wd / "empty.txt"

    result = main.fs_write(str(target), "")

    assert target.exists()
    assert target.read_text() == ""
    assert "Successfully wrote 0 characters" in result


def test_fs_write_multiline(tmp_wd):
    """fs_write handles multiline content."""
    target = tmp_wd / "multiline.txt"
    content = "line 1\nline 2\nline 3\n"

    result = main.fs_write(str(target), content)

    assert target.read_text() == content
    assert "Successfully wrote" in result


def test_fs_write_outside_wd(tmp_path):
    """fs_write returns error for paths outside working directory."""
    outside_file = tmp_path / "outside.txt"

    result = main.fs_write(str(outside_file), "content")

    assert result.startswith("Error:")
    assert "outside working directory" in result
    assert not outside_file.exists()
