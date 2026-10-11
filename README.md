# ai-swe-agent

Autonomous agent: give it a GitHub repo URL and a task, it plans, codes, tests, fixes, reviews,
scans, documents and opens a pull request.

## Quick start (local)
```bash
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill ANTHROPIC_API_KEY, GITHUB_TOKEN, SERVICE_API_KEY
pytest -q                   # unit + faked end-to-end graph test (no network needed)
python -m agent.cli https://github.com/<you>/demo-fastapi-app "Add JWT authentication"
```
Local runs default to `SANDBOX=docker` (Docker must be running). Set `SANDBOX=local` to skip Docker.

## API
```bash
uvicorn api.main:app --reload
curl -X POST localhost:8000/runs -H "x-api-key: $SERVICE_API_KEY" -H "content-type: application/json" \
  -d '{"repo_url":"https://github.com/<you>/demo-fastapi-app","task":"Add authentication"}'
curl localhost:8000/runs/<run_id>
```

## Safety
Works on a branch, never pushes to main, never auto-merges, path traversal blocked, fix attempts capped,
sandbox with timeout and memory cap. Use a fine-grained token scoped to specific repos.
