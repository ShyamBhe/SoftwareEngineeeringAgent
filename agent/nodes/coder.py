from .. import llm
from ..tools import repo

SYSTEM = """You are a senior engineer implementing a design. Output COMPLETE file contents (not diffs).
Match existing style. Add type hints. Never hardcode secrets; read them from environment variables.
Return JSON: {"files": [{"path": str, "content": str}]}"""


def coder(state):
    wd = state["workdir"]
    current = {f["path"]: repo.read_file(wd, f["path"]) for f in state["architecture"]["files"]}
    out = llm.ask_json(
        SYSTEM,
        f"Task: {state['task']}\nDesign: {state['architecture']}\nCurrent files: {current}",
        max_tokens=16000,
    )
    changed = []
    for f in out["files"]:
        repo.write_file(wd, f["path"], f["content"])
        changed.append(f["path"])
    deps = state["architecture"].get("new_dependencies", [])
    if deps:
        req = repo.read_file(wd, "requirements.txt")
        add = [d for d in deps if d.split("==")[0].lower() not in req.lower()]
        if add:
            repo.write_file(wd, "requirements.txt", req.rstrip() + "\n" + "\n".join(add) + "\n")
            changed.append("requirements.txt")
    return {"changed_files": changed, "events": state["events"] + [f"Coded {len(changed)} files"]}
