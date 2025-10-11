import pytest
from pathlib import Path
from ai import main


def test_fs_replace_single_occurrence(tmp_wd):
    """fs_replace replaces first occurrence by default."""
    test_file = tmp_wd / "test.txt"
    test_file.write_text("hello world\nhello again\n")

    result = main.fs_replace(str(test_file), "hello", "goodbye")

    content = test_file.read_text()
    assert content == "goodbye world\nhello again\n"
    assert result is None


def test_fs_replace_all_occurrences(tmp_wd):
    """fs_replace replaces all occurrences when replace_all is True."""
    test_file = tmp_wd / "test.txt"
    test_file.write_text("hello world\nhello again\nhello there\n")

    result = main.fs_replace(str(test_file), "hello", "goodbye", replace_all=True)

    content = test_file.read_text()
    assert content == "goodbye world\ngoodbye again\ngoodbye there\n"
    assert result is None


def test_fs_replace_multiline_string(tmp_wd):
    """fs_replace can replace multiline strings."""
    test_file = tmp_wd / "test.txt"
    test_file.write_text("line 1\nline 2\nline 3\n")

    result = main.fs_replace(str(test_file), "line 1\nline 2", "replaced")

    content = test_file.read_text()
    assert content == "replaced\nline 3\n"


def test_fs_replace_preserves_rest_of_file(tmp_wd):
    """fs_replace only changes the matched string."""
    test_file = tmp_wd / "test.txt"
    original = "prefix foo suffix\nother line\n"
    test_file.write_text(original)

    main.fs_replace(str(test_file), "foo", "bar")

    content = test_file.read_text()
    assert content == "prefix bar suffix\nother line\n"


def test_fs_replace_empty_old_string(tmp_wd):
    """fs_replace returns error for empty old_string."""
    test_file = tmp_wd / "test.txt"
    test_file.write_text("content")

    result = main.fs_replace(str(test_file), "", "new")

    assert result.startswith("Error:")
    assert "non-empty string" in result


def test_fs_replace_empty_new_string(tmp_wd):
    """fs_replace returns error for empty new_string."""
    test_file = tmp_wd / "test.txt"
    test_file.write_text("content")

    result = main.fs_replace(str(test_file), "old", "")

    assert result.startswith("Error:")
    assert "non-empty string" in result


def test_fs_replace_same_strings(tmp_wd):
    """fs_replace returns error when old and new are identical."""
    test_file = tmp_wd / "test.txt"
    test_file.write_text("content")

    result = main.fs_replace(str(test_file), "same", "same")

    assert result.startswith("Error:")
    assert "must be different" in result


def test_fs_replace_string_not_found(tmp_wd):
    """fs_replace returns error when old_string not found."""
    test_file = tmp_wd / "test.txt"
    original = "hello world"
    test_file.write_text(original)

    result = main.fs_replace(str(test_file), "nonexistent", "replacement")

    assert result.startswith("Error:")
    assert "not found" in result
    assert test_file.read_text() == original


def test_fs_replace_nonexistent_file(tmp_wd):
    """fs_replace returns error for nonexistent file."""
    nonexistent = tmp_wd / "does_not_exist.txt"

    result = main.fs_replace(str(nonexistent), "old", "new")

    assert result.startswith("Error:")
    assert "Error reading file" in result
