from .. import llm
from ..config import settings
from ..tools import repo, sandbox


def test_generator(state):
    wd = state["workdir"]
    code = {p: repo.read_file(wd, p) for p in state["changed_files"]}
    out = llm.ask_json(
        "Write pytest tests for the new behaviour: happy paths, failure paths, edge cases (bad token, "
        "duplicate user, wrong password). Use FastAPI TestClient. Tests must not need network or real secrets "
        'and must set needed env vars themselves. Return {"files": [{"path": str, "content": str}]}',
        f"Acceptance criteria: {state['plan']['acceptance_criteria']}\nCode:\n{code}",
        max_tokens=12000,
    )
    for f in out["files"]:
        repo.write_file(wd, f["path"], f["content"])
    paths = state["changed_files"] + [f["path"] for f in out["files"]]
    return {
        "changed_files": paths,
        "fix_attempts": 0,
        "events": state["events"] + [f"Generated {len(out['files'])} test files"],
    }


test_generator.__test__ = False  # not a pytest test


def test_runner(state):
    res = sandbox.run_tests(state["workdir"], state["repo_summary"].get("test_command"))
    tag = "PASS" if res["passed"] else "FAIL"
    return {"test_result": res, "events": state["events"] + [f"Tests {tag} (attempt {state.get('fix_attempts', 0)})"]}


test_runner.__test__ = False


def fixer(state):
    wd = state["workdir"]
    code = {p: repo.read_file(wd, p) for p in state["changed_files"]}
    out = llm.ask_json(
        "Tests failed. Diagnose the root cause from the output and fix it. Prefer fixing source code over "
        "weakening tests; only edit a test if it is genuinely wrong. Never delete tests or add skip markers. "
        'Return {"diagnosis": str, "files": [{"path": str, "content": str}]}',
        f"Test output:\n{state['test_result']['output']}\n\nFiles:\n{code}",
        max_tokens=16000,
    )
    for f in out["files"]:
        repo.write_file(wd, f["path"], f["content"])
    return {
        "fix_attempts": state.get("fix_attempts", 0) + 1,
        "events": state["events"] + [f"Fix: {out['diagnosis'][:120]}"],
    }


def route_after_tests(state) -> str:
    if state["test_result"]["passed"]:
        return "reviewer"
    return "fixer" if state.get("fix_attempts", 0) < settings.max_fix_attempts else "reviewer"
