import pytest
from pathlib import Path
from ai import main


def test_fs_rm_file(tmp_wd):
    """fs_rm deletes a file without confirmation."""
    test_file = tmp_wd / "delete_me.txt"
    test_file.write_text("content")

    result = main.fs_rm(str(test_file))

    assert not test_file.exists()
    assert "Successfully deleted file" in result


def test_fs_rm_empty_directory_with_confirmation(tmp_wd, monkeypatch):
    """fs_rm deletes empty directory with user confirmation."""
    test_dir = tmp_wd / "empty_dir"
    test_dir.mkdir()

    monkeypatch.setattr('builtins.input', lambda prompt: 'Y')

    result = main.fs_rm(str(test_dir))

    assert not test_dir.exists()
    assert "Successfully deleted directory" in result


def test_fs_rm_directory_with_contents(tmp_wd, monkeypatch):
    """fs_rm recursively deletes directory and all contents with confirmation."""
    test_dir = tmp_wd / "dir_with_stuff"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "file2.txt").write_text("content2")
    subdir = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("nested")

    monkeypatch.setattr('builtins.input', lambda prompt: 'Y')

    result = main.fs_rm(str(test_dir))

    assert not test_dir.exists()
    assert "Successfully deleted directory" in result
    assert "all its contents" in result


def test_fs_rm_directory_denied(tmp_wd, monkeypatch):
    """fs_rm does not delete directory when user denies."""
    test_dir = tmp_wd / "keep_me"
    test_dir.mkdir()
    (test_dir / "important.txt").write_text("important data")

    monkeypatch.setattr('builtins.input', lambda prompt: 'N')

    result = main.fs_rm(str(test_dir))

    assert test_dir.exists()
    assert (test_dir / "important.txt").exists()
    assert result.startswith("Error:")
    assert "denied" in result


def test_fs_rm_nonexistent(tmp_wd):
    """fs_rm returns error for nonexistent path."""
    nonexistent = tmp_wd / "does_not_exist"

    result = main.fs_rm(str(nonexistent))

    assert result.startswith("Error:")
    assert "does not exist" in result


def test_fs_rm_outside_wd(tmp_path):
    """fs_rm returns error for paths outside working directory."""
    outside = tmp_path / "outside.txt"
    outside.write_text("content")

    result = main.fs_rm(str(outside))

    assert result.startswith("Error:")
    assert "outside working directory" in result
    assert outside.exists()
