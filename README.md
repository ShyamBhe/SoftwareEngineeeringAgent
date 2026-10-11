# ai-swe-agent

An autonomous AI software engineering agent that takes a GitHub repository URL and a development task, then plans, implements, tests, fixes, reviews, scans, documents, and opens a pull request.

The goal is to automate repetitive software engineering work while keeping changes isolated, testable, and reviewable by a human.

## Features

- **Task planning:** breaks a development request into an implementation workflow.
- **Code generation:** makes changes in a working branch rather than directly on `main`.
- **Automated testing:** runs project tests and can make a bounded number of fix attempts.
- **Code review and security scanning:** checks proposed changes before publication.
- **Documentation:** updates or creates documentation relevant to the task.
- **Pull-request workflow:** prepares and opens a pull request for human review.
- **Sandboxed execution:** uses Docker by default, with execution limits configured for safety.
- **API access:** accepts tasks through a FastAPI endpoint protected by a service API key.
- **Testable workflow:** includes unit tests and a mocked end-to-end graph test that does not require network access.

## How it works

```text
GitHub repository + task
          |
          v
       Analyze
          |
          v
        Plan
          |
          v
      Architect
          |
          v
         Code
          |
          v
      Run tests
          |
      Pass or fail
       /       \
   Fix/retry   Continue
       \       /
          v
     Code review
          |
          v
   Security scanning
          |
          v
 Update documentation
          |
          v
   Open pull request
          |
          v
    Human review
```

The exact routing and order of stages are defined by the implementation in `agent/graph.py`. Fix attempts are capped to prevent unbounded execution.

## Tech stack

- Python 3.12
- FastAPI
- Anthropic API
- GitHub API / fine-grained GitHub tokens
- Docker sandboxing (default)
- Pytest

See `requirements.txt` and the source code for the current dependency list and implementation details.

## Requirements

Install or configure the following before running the agent:

- Python 3.12
- Git
- Docker Desktop / Docker Engine running for the default sandbox
- An Anthropic API key
- A GitHub fine-grained personal access token with only the permissions and repository access required by the workflow
- A service API key for protecting the HTTP API

## Quick start (local)

### 1. Create and activate a virtual environment

macOS / Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Create your local environment file:

```bash
cp .env.example .env
```

On Windows, copy the file with:

```powershell
Copy-Item .env.example .env
```

Set the required values in `.env`:

```dotenv
ANTHROPIC_API_KEY=your_anthropic_api_key
GITHUB_TOKEN=your_fine_grained_github_token
SERVICE_API_KEY=replace_with_a_long_random_secret
```

Use the exact variable names expected by the application's configuration. Do not commit `.env` or real credentials to Git.

### 4. Run the tests

```bash
pytest -q
```

The test suite includes unit tests and a mocked end-to-end graph test designed to run without network access. External integrations and live GitHub operations should be validated separately in a controlled test repository.

### 5. Run a task

Make sure Docker is running if you are using the default sandbox:

```bash
python -m agent.cli https://github.com/<YOUR_USERNAME>/demo-fastapi-app "Add JWT authentication"
```

Replace the example repository with a repository you are authorized to access and modify.

The task will use the sandbox and workflow configuration defined by the project. Review the resulting branch and pull request before accepting any changes.

## Sandbox configuration

The default is:

```dotenv
SANDBOX=docker
```

Docker must be running when Docker sandbox mode is selected.

To skip Docker and use the local execution mode:

```dotenv
SANDBOX=local
```

**Warning:** Local execution is less isolated than a properly restricted container. Use it only with repositories and tasks you trust. Do not run untrusted generated code on your host machine.

## API

### Start the FastAPI server

```bash
uvicorn api.main:app --reload
```

The local API is expected at `http://localhost:8000` while the server is running. FastAPI's interactive documentation is normally available at `http://localhost:8000/docs` if enabled by the application.

### Submit a task

Set `SERVICE_API_KEY` in your shell to the same value configured for the server, then submit a request:

```bash
curl -X POST http://localhost:8000/runs \
  -H "x-api-key: $SERVICE_API_KEY" \
  -H "content-type: application/json" \
  -d '{
    "repo_url": "https://github.com/<YOUR_USERNAME>/demo-fastapi-app",
    "task": "Add JWT authentication"
  }'
```

The response should provide a run identifier if the request is accepted. Use that identifier to check progress:

```bash
curl http://localhost:8000/runs/<RUN_ID> \
  -H "x-api-key: $SERVICE_API_KEY"
```

Replace `<RUN_ID>` with the identifier returned by the API. Confirm the actual response schema and endpoint behavior in `api/main.py` and the API documentation.

## Project structure

```text
ai-swe-agent/
├── agent/
│   ├── nodes/
│   │   ├── analyzer.py
│   │   ├── architect.py
│   │   ├── clone.py
│   │   ├── coder.py
│   │   ├── planner.py
│   │   ├── publish.py
│   │   ├── review.py
│   │   └── testing.py
│   ├── tools/
│   ├── cli.py
│   ├── config.py
│   ├── graph.py
│   ├── llm.py
│   └── state.py
├── api/
│   └── main.py
├── tests/
│   ├── test_graph.py
│   ├── test_routing.py
│   └── test_tools.py
├── .env.example
├── Dockerfile
├── requirements.txt
└── README.md
```

Individual modules may change as the project develops. Consult the source code for the authoritative implementation.

## Safety and security

The agent is designed with the following safeguards:

- **Branch isolation:** works on a branch and does not push directly to `main`.
- **No automatic merge:** pull requests are opened for human review; the agent does not auto-merge them.
- **Path traversal protection:** blocks attempts to escape permitted working paths.
- **Bounded repair loop:** limits the number of code-fix attempts.
- **Sandbox limits:** Docker execution is configured with timeout and memory limits.
- **Scoped GitHub credentials:** use a fine-grained token restricted to the specific repositories and permissions needed.
- **API authentication:** protect task-submission endpoints with `SERVICE_API_KEY`.
- **Secret hygiene:** keep API keys and tokens out of source control, prompts, logs, and generated artifacts.

These controls should be verified against the current implementation and deployment configuration. No sandbox or automated scan guarantees that code is completely safe. Review changes and permissions before using the agent with sensitive repositories.

## Troubleshooting

### Docker is unavailable

Start Docker Desktop / Docker Engine and check:

```bash
docker info
```

If you intentionally want to run without Docker, set `SANDBOX=local` in `.env` and understand the reduced isolation.

### API key or GitHub authentication fails

- Check the variable names in `.env` against `agent/config.py`.
- Confirm the token has access to the target repository and the required permissions.
- Restart the process after changing environment variables.
- Never paste secrets into an issue, commit, or public log.

### Tests fail

```bash
pytest -q
```

Read the first failing test and its traceback. Confirm dependencies are installed and configuration-dependent tests use mocks or appropriate test credentials.

### API does not start

- Activate the virtual environment.
- Install dependencies from `requirements.txt`.
- Run Uvicorn from the project root.
- Check the terminal for missing environment variables, import errors, or port conflicts.

## Roadmap

Potential improvements include:

- [ ] CI pipeline for linting, type checking, tests, and dependency scanning.
- [ ] Structured logs and traceable run history.
- [ ] Clear per-stage status and failure reporting through the API.
- [ ] Integration tests using a dedicated disposable GitHub repository.
- [ ] More detailed summaries of diffs, test results, and security findings in pull requests.
- [ ] Configurable model and execution policies.
- [ ] Stronger isolation and resource limits for untrusted code.

## Contributing

Contributions are welcome.

1. Create a feature branch.
2. Make a focused change and add or update tests.
3. Run `pytest -q`.
4. Check that no credentials, tokens, or private data are included.
5. Open a pull request describing the change, test coverage, and known limitations.

## License

No license is specified yet. Add a `LICENSE` file before distributing the project or accepting external contributions.
