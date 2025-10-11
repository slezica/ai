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


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess.run for shell command tests."""
    mock = Mock()
    mock.return_value = Mock(
        returncode=0,
        stdout="mock output",
        stderr=""
    )
    monkeypatch.setattr('subprocess.run', mock)
    return mock


@pytest.fixture
def mock_kagi(monkeypatch):
    """Mock Kagi API client for web tests."""
    mock_client = MagicMock()

    mock_client.search.return_value = {
        "data": [
            {
                "t": 0,
                "title": "Test Result",
                "url": "https://example.com",
                "published": "2024-01-01",
                "snippet": "Test snippet"
            }
        ]
    }

    mock_client.summarize.return_value = {
        "data": {
            "output": "Test summary"
        }
    }

    monkeypatch.setattr('ai.main.kagi_client', mock_client)
    return mock_client


@pytest.fixture
def mock_lms(monkeypatch):
    """Mock LMStudio for integration tests."""
    mock_model = MagicMock()
    mock_chat = MagicMock()

    monkeypatch.setattr('lmstudio.llm', lambda x: mock_model)
    monkeypatch.setattr('lmstudio.Chat', lambda x: mock_chat)

    return {
        'model': mock_model,
        'chat': mock_chat
    }


@pytest.fixture(autouse=True)
def reset_shell_permissions():
    """Reset shell allowed/forbidden lists between tests."""
    from ai import main
    main.shell_allowed.clear()
    main.shell_forbidden.clear()
    yield
