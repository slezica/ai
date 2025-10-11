import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def tmp_wd(tmp_path, monkeypatch):
    """Temporary working directory for isolated file operations."""
    monkeypatch.setattr('ai.main.WD', str(tmp_path))
    return tmp_path


