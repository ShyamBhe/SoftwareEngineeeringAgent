import sys
import uuid

from .graph import build_graph

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit('usage: python -m agent.cli <repo_url> "<task>"')
    repo_url, task = sys.argv[1], sys.argv[2]
    run_id = uuid.uuid4().hex[:8]
    final = build_graph().invoke({"run_id": run_id, "task": task, "repo_url": repo_url, "events": []})
    print("\n".join(final["events"]))
    print("PR:", final.get("pr_url"))
