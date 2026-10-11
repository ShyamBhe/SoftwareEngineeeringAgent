import os
import re
import shutil
import tempfile
from pathlib import Path

from git import Repo
from github import Github

from ..config import settings

IGNORE = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build"}
MAX_FILE_CHARS = 12_000


def clone(repo_url: str, run_id: str) -> tuple[str, str]:
    workdir = tempfile.mkdtemp(prefix=f"run-{run_id}-")
    auth_url = repo_url.replace("https://", f"https://x-access-token:{settings.github_token}@")
    repo = Repo.clone_from(auth_url, workdir, depth=50)
    branch = f"agent/{run_id}"
    repo.git.checkout("-b", branch)
    return workdir, branch


def tree(workdir: str, max_files: int = 400) -> list[str]:
    out = []
    for root, dirs, files in os.walk(workdir):
        dirs[:] = [d for d in dirs if d not in IGNORE]
        for f in files:
            out.append(os.path.relpath(os.path.join(root, f), workdir))
    return sorted(out)[:max_files]


def _safe(workdir: str, rel: str) -> Path:
    root = Path(workdir).resolve()
    p = (root / rel).resolve()
    if p != root and root not in p.parents:
        raise ValueError(f"Path escapes repo: {rel}")
    if ".git" in p.relative_to(root).parts:
        raise ValueError("Refusing to touch .git")
    return p


def read_file(workdir: str, rel: str) -> str:
    p = _safe(workdir, rel)
    return p.read_text(errors="replace")[:MAX_FILE_CHARS] if p.exists() else ""


def write_file(workdir: str, rel: str, content: str) -> None:
    p = _safe(workdir, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def diff(workdir: str) -> str:
    repo = Repo(workdir)
    repo.git.add("-A")
    return repo.git.diff("--cached")[:60_000]


def commit_and_push(workdir: str, branch: str, message: str) -> None:
    repo = Repo(workdir)
    repo.git.add("-A")
    repo.git.config("user.name", "ai-swe-agent")
    repo.git.config("user.email", "agent@users.noreply.github.com")
    repo.index.commit(message)
    repo.remote().push(refspec=f"{branch}:{branch}")


def open_pr(repo_url: str, branch: str, title: str, body: str) -> str:
    slug = re.sub(r"^https://github.com/|\.git$|/$", "", repo_url)
    gh_repo = Github(settings.github_token).get_repo(slug)
    pr = gh_repo.create_pull(title=title, body=body, head=branch, base=gh_repo.default_branch, draft=False)
    return pr.html_url


def cleanup(workdir: str) -> None:
    shutil.rmtree(workdir, ignore_errors=True)
