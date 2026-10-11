from ..tools import repo


def clone_repo(state):
    wd, branch = repo.clone(state["repo_url"], state["run_id"])
    return {"workdir": wd, "branch": branch, "events": state.get("events", []) + [f"Cloned into branch {branch}"]}
