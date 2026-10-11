from .. import llm
from ..tools import repo, sandbox


def reviewer(state):
    d = repo.diff(state["workdir"])
    review = llm.ask_json(
        "You are a strict code reviewer. Check correctness, style, error handling, test quality and that "
        'the diff satisfies the acceptance criteria. Return {"verdict": "approve"|"concerns", '
        '"issues": [{"severity": str, "file": str, "note": str}], "summary": str}',
        f"Criteria: {state['plan']['acceptance_criteria']}\nTests passed: {state['test_result']['passed']}\nDiff:\n{d}",
    )
    return {"review": review, "events": state["events"] + [f"Review: {review['verdict']}"]}


def security_checker(state):
    scans = sandbox.run_security_scans(state["workdir"])
    d = repo.diff(state["workdir"])
    sec = llm.ask_json(
        "You are an application security engineer. Using the scanner output and the diff, report real "
        "issues: hardcoded secrets, weak hashing, missing token expiry, injection, unsafe defaults. "
        'Return {"risk": "low"|"medium"|"high", "findings": [str], "scanner_notes": str}',
        f"Bandit:\n{scans['bandit']['output']}\npip-audit:\n{scans['pip_audit']['output']}\nDiff:\n{d}",
    )
    return {"security": sec, "events": state["events"] + [f"Security risk: {sec['risk']}"]}
