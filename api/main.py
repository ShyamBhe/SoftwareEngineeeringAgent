import hmac
import uuid

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from pydantic import BaseModel, HttpUrl

from agent.config import settings
from agent.graph import build_graph
from agent.tools import repo

app = FastAPI(title="AI Software Engineering Agent")
RUNS: dict[str, dict] = {}  # swap for Redis or Postgres in production


class RunRequest(BaseModel):
    repo_url: HttpUrl
    task: str


def execute(run_id: str, repo_url: str, task: str):
    workdir = None
    try:
        RUNS[run_id]["status"] = "running"
        for update in build_graph().stream(
            {"run_id": run_id, "task": task, "repo_url": repo_url, "events": []},
            stream_mode="values",
        ):
            workdir = update.get("workdir", workdir)
            RUNS[run_id]["events"] = update.get("events", [])
            RUNS[run_id]["pr_url"] = update.get("pr_url")
        RUNS[run_id]["status"] = "done"
    except Exception as e:  # noqa: BLE001
        RUNS[run_id]["status"] = "failed"
        RUNS[run_id]["error"] = str(e)
    finally:
        if workdir:
            repo.cleanup(workdir)


@app.post("/runs")
def create_run(req: RunRequest, bg: BackgroundTasks, x_api_key: str = Header(...)):
    if not settings.service_api_key or not hmac.compare_digest(x_api_key, settings.service_api_key):
        raise HTTPException(401, "bad key")
    run_id = uuid.uuid4().hex[:8]
    RUNS[run_id] = {"status": "queued", "events": [], "pr_url": None}
    bg.add_task(execute, run_id, str(req.repo_url), req.task)
    return {"run_id": run_id}


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(404)
    return RUNS[run_id]


@app.get("/healthz")
def health():
    return {"ok": True}
