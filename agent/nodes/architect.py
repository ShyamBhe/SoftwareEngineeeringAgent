from .. import llm

SYSTEM = """You are a software architect. Given the task, plan and repo summary, design the change.
Follow the repo's existing conventions. Prefer minimal, reversible changes.
Return JSON: {"design": str, "files": [{"path": str, "action": "create"|"modify", "purpose": str}],
"new_dependencies": [str], "env_vars": [str]}
For authentication in FastAPI prefer: JWT access tokens, password hashing with a vetted library,
a reusable get_current_user dependency, secrets from environment variables, never hardcoded."""


def architect(state):
    ctx = "\n\n".join(f"### {p}\n{c}" for p, c in state["context_files"].items())
    arch = llm.ask_json(
        SYSTEM,
        f"Task: {state['task']}\nPlan: {state['plan']}\nRepo: {state['repo_summary']}\n\n{ctx}",
    )
    return {"architecture": arch, "events": state["events"] + [f"Architecture: {len(arch['files'])} files to change"]}
