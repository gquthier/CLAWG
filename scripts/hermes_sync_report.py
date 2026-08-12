#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


HIGH_RISK_PREFIXES = [
    ".github/workflows/tests.yml",
    "pyproject.toml",
    "run_agent.py",
    "model_tools.py",
    "toolsets.py",
    "cli.py",
    "gateway/",
    "cron/",
    "clawg_cli/main.py",
    "clawg_cli/config.py",
    "clawg_cli/setup.py",
    "clawg_cli/auth.py",
    "tools/browser_tool.py",
    "tools/mcp_tool.py",
    "tools/memory_tool.py",
    "tools/delegate_tool.py",
    "tools/terminal_tool.py",
    "tools/approval.py",
    "scripts/install.sh",
    "scripts/install.cmd",
    "scripts/install.ps1",
]

MEDIUM_RISK_PREFIXES = [
    "agent/",
    "tools/",
    "tests/",
    "clawg_cli/",
    "gateway/platforms/",
    "acp_adapter/",
    "environments/",
]

PROTECTED_LOCAL_PREFIXES = [
    "AGENTS.md",
    "README.md",
    "website/",
    "landingpage/",
    "subagents/",
    "optional-skills/",
    "dashboard/",
]

IMPORTANT_KEYWORDS = (
    "memory",
    "provider",
    "browser",
    "telegram",
    "security",
    "credential",
    "profile",
    "gateway",
    "tool",
    "install",
)


@dataclass
class Report:
    repo_root: str
    base_branch: str
    upstream_remote: str
    upstream_branch: str
    local_head: str
    upstream_head: str
    merge_base: str
    local_only_commits: int
    upstream_only_commits: int
    changed_files_count: int
    risk_level: str
    important_update: bool
    protected_local_touched: list[str]
    high_risk_files: list[str]
    medium_risk_files: list[str]
    low_risk_files: list[str]
    changed_files: list[str]
    summary_markdown: str


def run_git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed with code {result.returncode}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def ensure_upstream(repo: Path, remote: str, url: str, branch: str) -> None:
    existing = run_git(repo, "remote", check=False)
    remotes = {line.strip() for line in existing.splitlines() if line.strip()}
    if remote not in remotes:
        run_git(repo, "remote", "add", remote, url)
    run_git(repo, "fetch", remote, branch, "--prune")


def commit_count(repo: Path, rev_range: str) -> int:
    output = run_git(repo, "rev-list", "--count", rev_range)
    return int(output or "0")


def changed_files(repo: Path, merge_base: str, upstream_ref: str) -> list[str]:
    output = run_git(repo, "diff", "--name-only", f"{merge_base}..{upstream_ref}")
    return [line.strip() for line in output.splitlines() if line.strip()]


def classify(path: str) -> str:
    if any(path == prefix or path.startswith(prefix) for prefix in PROTECTED_LOCAL_PREFIXES):
        return "protected"
    if any(path == prefix or path.startswith(prefix) for prefix in HIGH_RISK_PREFIXES):
        return "high"
    if any(path == prefix or path.startswith(prefix) for prefix in MEDIUM_RISK_PREFIXES):
        return "medium"
    return "low"


def is_important(paths: Iterable[str]) -> bool:
    for path in paths:
        lowered = path.lower()
        if classify(path) in {"high", "protected"}:
            return True
        if any(keyword in lowered for keyword in IMPORTANT_KEYWORDS):
            return True
    return False


def build_markdown(report: Report) -> str:
    def bullets(items: list[str], empty: str) -> str:
        if not items:
            return f"- {empty}"
        return "\n".join(f"- `{item}`" for item in items[:25])

    return f"""# Hermes Upstream Sync Report

- Repo: `{report.repo_root}`
- Base branch: `{report.base_branch}`
- Upstream: `{report.upstream_remote}/{report.upstream_branch}`
- Local head: `{report.local_head}`
- Upstream head: `{report.upstream_head}`
- Merge base: `{report.merge_base}`
- Local-only commits: `{report.local_only_commits}`
- Upstream-only commits: `{report.upstream_only_commits}`
- Changed files since merge-base: `{report.changed_files_count}`
- Risk level: `{report.risk_level}`
- Important update: `{str(report.important_update).lower()}`

## High risk files
{bullets(report.high_risk_files, 'No high-risk files detected')}

## Medium risk files
{bullets(report.medium_risk_files, 'No medium-risk files detected')}

## Protected CLAWG-local files touched upstream
{bullets(report.protected_local_touched, 'No protected local files touched upstream')}

## Low risk files
{bullets(report.low_risk_files, 'No low-risk files detected')}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Hermes upstream sync risk report for CLAWG.")
    parser.add_argument("--repo", default=".", help="Path to the CLAWG repository")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--upstream-remote", default="upstream")
    parser.add_argument("--upstream-url", default="https://github.com/NousResearch/hermes-agent.git")
    parser.add_argument("--upstream-branch", default="main")
    parser.add_argument("--json-out", help="Write report JSON to this path")
    parser.add_argument("--md-out", help="Write report markdown to this path")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    ensure_upstream(repo, args.upstream_remote, args.upstream_url, args.upstream_branch)

    upstream_ref = f"{args.upstream_remote}/{args.upstream_branch}"
    local_head = run_git(repo, "rev-parse", args.base_branch)
    upstream_head = run_git(repo, "rev-parse", upstream_ref)
    merge_base = run_git(repo, "merge-base", args.base_branch, upstream_ref)

    local_only = commit_count(repo, f"{upstream_ref}..{args.base_branch}")
    upstream_only = commit_count(repo, f"{args.base_branch}..{upstream_ref}")
    paths = changed_files(repo, merge_base, upstream_ref)

    high = [path for path in paths if classify(path) == "high"]
    medium = [path for path in paths if classify(path) == "medium"]
    protected = [path for path in paths if classify(path) == "protected"]
    low = [path for path in paths if classify(path) == "low"]

    if not paths:
        risk = "none"
    elif high or protected:
        risk = "high"
    elif medium:
        risk = "medium"
    else:
        risk = "low"

    report = Report(
        repo_root=str(repo),
        base_branch=args.base_branch,
        upstream_remote=args.upstream_remote,
        upstream_branch=args.upstream_branch,
        local_head=local_head,
        upstream_head=upstream_head,
        merge_base=merge_base,
        local_only_commits=local_only,
        upstream_only_commits=upstream_only,
        changed_files_count=len(paths),
        risk_level=risk,
        important_update=is_important(paths),
        protected_local_touched=protected,
        high_risk_files=high,
        medium_risk_files=medium,
        low_risk_files=low,
        changed_files=paths,
        summary_markdown="",
    )
    report.summary_markdown = build_markdown(report)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8")
    if args.md_out:
        Path(args.md_out).write_text(report.summary_markdown, encoding="utf-8")

    if args.print_json:
        print(json.dumps(asdict(report), indent=2))
    else:
        print(report.summary_markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
