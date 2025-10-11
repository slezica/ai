import pytest
from unittest.mock import Mock
from ai import main


def test_shell_command_allowed(mock_subprocess, monkeypatch):
    """shell executes command when permission granted with 'Y'."""
    monkeypatch.setattr('builtins.input', lambda prompt: 'Y')

    result = main.shell('ls', ['-la'])

    assert result == "Success (exit code 0):\nmock output"
    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args[0][0]
    assert call_args == ['ls', '-la']


def test_shell_command_always_allow(mock_subprocess, monkeypatch):
    """shell adds command to allowed list when 'A' is chosen."""
    monkeypatch.setattr('builtins.input', lambda prompt: 'A')

    result = main.shell('git', ['status'])

    assert result == "Success (exit code 0):\nmock output"
    assert 'git' in main.shell_allowed

    # Second call should not prompt
    mock_subprocess.reset_mock()
    result = main.shell('git', ['log'])
    assert result == "Success (exit code 0):\nmock output"


def test_shell_command_denied_no(mock_subprocess, monkeypatch):
    """shell returns error when permission denied with 'N'."""
    monkeypatch.setattr('builtins.input', lambda prompt: 'N')

    result = main.shell('rm', ['-rf'])

    assert result.startswith("Error:")
    assert "denied" in result
    mock_subprocess.assert_not_called()


def test_shell_command_never_allow(mock_subprocess, monkeypatch):
    """shell adds command to forbidden list when 'X' is chosen."""
    monkeypatch.setattr('builtins.input', lambda prompt: 'X')

    result = main.shell('dangerous', ['command'])

    assert result.startswith("Error:")
    assert "denied" in result
    assert 'dangerous' in main.shell_forbidden
    mock_subprocess.assert_not_called()


def test_shell_command_already_forbidden(mock_subprocess):
    """shell rejects command already in forbidden list."""
    main.shell_forbidden.append('blocked')

    result = main.shell('blocked', ['args'])

    assert result.startswith("Error:")
    assert "forbidden" in result
    mock_subprocess.assert_not_called()


def test_shell_command_already_allowed(mock_subprocess):
    """shell runs command already in allowed list without prompting."""
    main.shell_allowed.append('trusted')

    result = main.shell('trusted', ['args'])

    assert result == "Success (exit code 0):\nmock output"
    mock_subprocess.assert_called_once()


def test_shell_nonzero_exit_code(mock_subprocess, monkeypatch):
    """shell returns error message for non-zero exit codes."""
    monkeypatch.setattr('builtins.input', lambda prompt: 'Y')
    mock_subprocess.return_value = Mock(
        returncode=1,
        stdout="error output",
        stderr=""
    )

    result = main.shell('failing', ['command'])

    assert result.startswith("Error (exit code 1):")
    assert "error output" in result


def test_shell_empty_output(mock_subprocess, monkeypatch):
    """shell handles empty stdout."""
    monkeypatch.setattr('builtins.input', lambda prompt: 'Y')
    mock_subprocess.return_value = Mock(
        returncode=0,
        stdout="",
        stderr=""
    )

    result = main.shell('silent', ['command'])

    assert result == "Success (exit code 0):\n(no output)"


def test_shell_default_denial(mock_subprocess, monkeypatch):
    """shell denies command by default on invalid input."""
    monkeypatch.setattr('builtins.input', lambda prompt: 'invalid')

    result = main.shell('echo', ['test'])

    assert result.startswith("Error:")
    assert "denied" in result
    mock_subprocess.assert_not_called()


def test_shell_arguments_passed_correctly(mock_subprocess, monkeypatch):
    """shell passes arguments to subprocess correctly."""
    monkeypatch.setattr('builtins.input', lambda prompt: 'Y')

    main.shell('cmd', ['arg1', 'arg2', 'arg3'])

    call_args = mock_subprocess.call_args[0][0]
    assert call_args == ['cmd', 'arg1', 'arg2', 'arg3']
