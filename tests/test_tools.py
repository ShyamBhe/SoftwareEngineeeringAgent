import pytest

from agent.tools import repo


def test_path_traversal_blocked(tmp_path):
    with pytest.raises(ValueError):
        repo.write_file(str(tmp_path), "../evil.txt", "x")


def test_git_dir_blocked(tmp_path):
    with pytest.raises(ValueError):
        repo.write_file(str(tmp_path), ".git/config", "x")


def test_roundtrip(tmp_path):
    repo.write_file(str(tmp_path), "a/b.py", "print(1)")
    assert repo.read_file(str(tmp_path), "a/b.py") == "print(1)"
