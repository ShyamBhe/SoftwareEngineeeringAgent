import subprocess

from ..config import settings

TIMEOUT = 300


def run(workdir: str, cmd: str) -> dict:
    if settings.sandbox == "docker":
        full = ["docker", "run", "--rm", "--memory=1g", "--cpus=1",
                "-v", f"{workdir}:/work", "-w", "/work",
                "python:3.12-slim", "sh", "-c", cmd]
    else:  # local mode: only when the container itself is the sandbox
        full = ["sh", "-c", cmd]
    try:
        p = subprocess.run(full, cwd=workdir, capture_output=True, text=True, timeout=TIMEOUT)
        return {"passed": p.returncode == 0, "output": (p.stdout + p.stderr)[-8000:]}
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": f"Timed out after {TIMEOUT}s"}


def run_tests(workdir: str, test_cmd: str | None) -> dict:
    cmd = test_cmd or "pip install -q -r requirements.txt pytest httpx && pytest -x -q"
    return run(workdir, cmd)


def run_security_scans(workdir: str) -> dict:
    bandit = run(workdir, "pip install -q bandit && bandit -r . -x ./tests,./.venv -ll -q")
    audit = run(workdir, "pip install -q pip-audit && pip-audit -r requirements.txt")
    return {"bandit": bandit, "pip_audit": audit}
