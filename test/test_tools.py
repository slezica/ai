import pytest
from ai import main


def test_fs_pwd(tmp_wd):
    """fs_pwd returns the current working directory."""
    result = main.fs_pwd()

    assert result == str(tmp_wd)
