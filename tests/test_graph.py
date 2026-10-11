"""End-to-end graph test with the LLM, GitHub and sandbox all faked."""
from git import Repo

from agent import llm
from agent.graph import build_graph
from agent.tools import repo, sandbox


def _fake_json(system, user, max_tokens=8000):
    if "planning a change" in system:
        return {"goal": "Add feature", "steps": ["a", "b"], "risks": [], "needs_new_dependencies": [],
                "acceptance_criteria": ["works"]}
    if "exploring a repo" in system:
        return {"files": ["main.py"]}
    if "Summarize this repo" in system:
        return {"framework": "FastAPI", "entrypoint": "main.py", "structure": "flat", "test_command": None,
                "conventions": [], "dependencies_file": None}
    if "software architect" in system:
        return {"design": "d", "files": [{"path": "main.py", "action": "modify", "purpose": "p"}],
                "new_dependencies": [], "env_vars": []}
    if "implementing a design" in system:
        return {"files": [{"path": "main.py", "content": "print('new')\n"}]}
    if "Write pytest tests" in system:
        return {"files": [{"path": "tests/test_new.py", "content": "def test_x():\n    assert True\n"}]}
    if "Tests failed" in system:
        return {"diagnosis": "fixed it", "files": [{"path": "main.py", "content": "print('fixed')\n"}]}
    if "code reviewer" in system:
        return {"verdict": "approve", "issues": [], "summary": "looks good"}
    if "security engineer" in system:
        return {"risk": "low", "findings": [], "scanner_notes": ""}
    raise AssertionError(f"unexpected prompt: {system[:60]}")


def test_full_pipeline_with_one_fix(monkeypatch, tmp_path):
    def fake_clone(url, run_id):
        wd = tmp_path / "work"
        wd.mkdir()
        r = Repo.init(wd)
        r.git.config("user.name", "t")
        r.git.config("user.email", "t@t")
        (wd / "main.py").write_text("print('old')\n")
        (wd / "README.md").write_text("# demo\n")
        r.git.add("-A")
        r.index.commit("init")
        r.git.checkout("-b", f"agent/{run_id}")
        return str(wd), f"agent/{run_id}"

    results = iter([{"passed": False, "output": "boom"}, {"passed": True, "output": "ok"}])
    pushed = {}

    monkeypatch.setattr(llm, "ask_json", _fake_json)
    monkeypatch.setattr(llm, "ask", lambda s, u, m=8000: "## New feature\nDocs.")
    monkeypatch.setattr(repo, "clone", fake_clone)
    monkeypatch.setattr(repo, "commit_and_push", lambda wd, b, m: pushed.update(branch=b))
    monkeypatch.setattr(repo, "open_pr", lambda *a: "https://github.com/x/y/pull/1")
    monkeypatch.setattr(sandbox, "run_tests", lambda wd, cmd: next(results))
    monkeypatch.setattr(sandbox, "run_security_scans",
                        lambda wd: {"bandit": {"output": ""}, "pip_audit": {"output": ""}})

    final = build_graph().invoke({"run_id": "abc12345", "task": "t", "repo_url": "https://github.com/x/y",
                                  "events": []})
    assert final["pr_url"].endswith("/pull/1")
    assert final["fix_attempts"] == 1
    assert pushed["branch"] == "agent/abc12345"
    assert any("Tests FAIL" in e for e in final["events"])
    assert any("Tests PASS" in e for e in final["events"])
