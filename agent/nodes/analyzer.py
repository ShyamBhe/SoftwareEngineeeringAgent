from .. import llm
from ..tools import repo


def analyzer(state):
    wd = state["workdir"]
    files = repo.tree(wd)
    pick = llm.ask_json(
        "You are exploring a repo to prepare for a change. From the file list choose up to 15 files most "
        "relevant to the task (entrypoint, routers, models, config, requirements, existing tests). "
        'Return {"files": [paths]}.',
        f"Task: {state['task']}\nPlan: {state['plan']}\nFiles:\n" + "\n".join(files),
    )["files"]
    ctx = {p: repo.read_file(wd, p) for p in pick if p in files}
    summary = llm.ask_json(
        "Summarize this repo for another engineer. Return JSON: "
        '{"framework": str, "entrypoint": str, "structure": str, "test_command": str|null, '
        '"conventions": [str], "dependencies_file": str|null}',
        "\n\n".join(f"### {p}\n{c}" for p, c in ctx.items()),
    )
    return {
        "context_files": ctx,
        "repo_summary": summary,
        "events": state["events"] + [f"Analyzed repo ({summary['framework']}), read {len(ctx)} files"],
    }
