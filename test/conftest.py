import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def tmp_wd(tmp_path, monkeypatch):
    """Temporary working directory for isolated file operations."""
    monkeypatch.setattr('ai.main.WD', str(tmp_path))
    return tmp_path


@pytest.fixture
def sample_file(tmp_wd):
    """Create a sample text file with known content."""
    file_path = tmp_wd / "sample.txt"
    content = "line 1\nline 2\nline 3\nline 4\nline 5\n"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_dir(tmp_wd):
    """Create a sample directory structure."""
    dir_path = tmp_wd / "sample_dir"
    dir_path.mkdir()

    (dir_path / "file1.txt").write_text("content 1")
    (dir_path / "file2.txt").write_text("content 2")
    (dir_path / "subdir").mkdir()
    (dir_path / "subdir" / "nested.txt").write_text("nested content")

    return dir_path


