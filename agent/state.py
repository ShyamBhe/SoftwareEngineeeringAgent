from typing import TypedDict


class AgentState(TypedDict, total=False):
    run_id: str
    task: str
    repo_url: str
    workdir: str
    branch: str
    plan: dict
    repo_summary: dict
    context_files: dict
    architecture: dict
    changed_files: list
    test_result: dict
    fix_attempts: int
    review: dict
    security: dict
    docs_summary: str
    pr_url: str
    events: list
