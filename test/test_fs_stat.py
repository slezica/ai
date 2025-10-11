import pytest
from pathlib import Path
from ai import main


def test_fs_stat_file(sample_file):
    """fs_stat returns file metadata."""
    result = main.fs_stat(str(sample_file))

    actual_stat = sample_file.stat()

    lines = result.split('\n')
    assert len(lines) == 6

    assert lines[0] == f'size: {actual_stat.st_size}'
    assert lines[1].startswith('created: ')
    assert lines[2] == f'modified: {actual_stat.st_mtime}'
    assert lines[3] == f'accessed: {actual_stat.st_atime}'
    assert lines[4] == 'type: f'
    assert lines[5] == f'permissions: {oct(actual_stat.st_mode)[-3:]}'


def test_fs_stat_directory(sample_dir):
    """fs_stat returns directory metadata."""
    result = main.fs_stat(str(sample_dir))

    actual_stat = sample_dir.stat()

    lines = result.split('\n')
    assert len(lines) == 6

    assert lines[0] == f'size: {actual_stat.st_size}'
    assert lines[1].startswith('created: ')
    assert lines[2] == f'modified: {actual_stat.st_mtime}'
    assert lines[3] == f'accessed: {actual_stat.st_atime}'
    assert lines[4] == 'type: d'
    assert lines[5] == f'permissions: {oct(actual_stat.st_mode)[-3:]}'


def test_fs_stat_nonexistent(tmp_wd):
    """fs_stat returns error for nonexistent path."""
    nonexistent = tmp_wd / "does_not_exist.txt"

    result = main.fs_stat(str(nonexistent))

    assert result.startswith("Error:")
    assert "does not exist" in result


def test_fs_stat_outside_wd(tmp_path):
    """fs_stat returns error for paths outside working directory."""
    outside_path = tmp_path / "outside.txt"
    outside_path.write_text("content")

    result = main.fs_stat(str(outside_path))

    assert result.startswith("Error:")
    assert "outside working directory" in result
