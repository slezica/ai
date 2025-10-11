import pytest
from pathlib import Path
from ai import main


def test_fs_search_finds_matches(tmp_wd):
    """fs_search finds and returns matching lines."""
    file1 = tmp_wd / "file1.txt"
    file2 = tmp_wd / "file2.txt"
    file1.write_text("hello world\nfoo bar\n")
    file2.write_text("hello there\nbaz qux\n")

    result = main.fs_search(str(tmp_wd), "hello")

    assert "file1.txt" in result
    assert "file2.txt" in result
    assert "hello world" in result
    assert "hello there" in result


def test_fs_search_line_numbers(tmp_wd):
    """fs_search includes line numbers in output."""
    test_file = tmp_wd / "test.txt"
    test_file.write_text("line 1\nline 2\nmatching line\nline 4\n")

    result = main.fs_search(str(tmp_wd), "matching")

    assert ":3:" in result
    assert "matching line" in result


def test_fs_search_no_matches(tmp_wd):
    """fs_search returns empty string when no matches found."""
    test_file = tmp_wd / "test.txt"
    test_file.write_text("hello world\n")

    result = main.fs_search(str(tmp_wd), "nonexistent")

    assert result == ""


def test_fs_search_regex_pattern(tmp_wd):
    """fs_search supports regex patterns."""
    test_file = tmp_wd / "test.txt"
    test_file.write_text("test123\ntest456\nabc789\n")

    result = main.fs_search(str(tmp_wd), r"test\d+")

    assert "test123" in result
    assert "test456" in result
    assert "abc789" not in result


def test_fs_search_single_file(tmp_wd):
    """fs_search can search a single file."""
    test_file = tmp_wd / "single.txt"
    test_file.write_text("find me\ndon't find this\n")

    result = main.fs_search(str(test_file), "find me")

    assert "find me" in result
    assert "don't find this" not in result


def test_fs_search_nonexistent(tmp_wd):
    """fs_search returns error for nonexistent path."""
    nonexistent = tmp_wd / "does_not_exist"

    result = main.fs_search(str(nonexistent), "pattern")

    assert result.startswith("Error:")
    assert "does not exist" in result


def test_fs_search_outside_wd(tmp_path):
    """fs_search returns error for paths outside working directory."""
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()

    result = main.fs_search(str(outside_dir), "pattern")

    assert result.startswith("Error:")
    assert "outside working directory" in result
