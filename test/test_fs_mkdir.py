import pytest
from pathlib import Path
from ai import main


def test_fs_mkdir_simple(tmp_wd):
    """fs_mkdir creates a simple directory."""
    new_dir = tmp_wd / "new_directory"

    result = main.fs_mkdir(str(new_dir))

    assert new_dir.exists()
    assert new_dir.is_dir()
    assert "Successfully created directory" in result


def test_fs_mkdir_nested(tmp_wd):
    """fs_mkdir creates nested directories recursively."""
    nested = tmp_wd / "level1" / "level2" / "level3"

    result = main.fs_mkdir(str(nested))

    assert nested.exists()
    assert nested.is_dir()
    assert (tmp_wd / "level1").exists()
    assert (tmp_wd / "level1" / "level2").exists()


def test_fs_mkdir_already_exists(tmp_wd):
    """fs_mkdir returns error when path already exists."""
    existing = tmp_wd / "existing"
    existing.mkdir()

    result = main.fs_mkdir(str(existing))

    assert result.startswith("Error:")
    assert "already exists" in result


def test_fs_mkdir_file_exists(tmp_wd):
    """fs_mkdir returns error when a file exists at path."""
    existing_file = tmp_wd / "file.txt"
    existing_file.write_text("content")

    result = main.fs_mkdir(str(existing_file))

    assert result.startswith("Error:")
    assert "already exists" in result


def test_fs_mkdir_outside_wd(tmp_path):
    """fs_mkdir returns error for paths outside working directory."""
    outside = tmp_path / "outside"

    result = main.fs_mkdir(str(outside))

    assert result.startswith("Error:")
    assert "outside working directory" in result
    assert not outside.exists()
