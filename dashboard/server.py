"""
CLAWG Command Center — Local API Server

Serves vault data (agents, crons, tasks, projects, skills) as JSON
for the Command Center dashboard.

Usage:
    python dashboard/server.py [--port 9777]
    clawg dashboard  (preferred — auto-opens browser)
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

# ─── Paths ───

CLAWG_ROOT = Path(__file__).resolve().parent.parent
CLAWG_HOME = Path(os.getenv("CLAWG_HOME", Path.home() / ".clawg"))
DASHBOARD_DIR = CLAWG_ROOT / "dashboard"
SUBAGENTS_DIR = CLAWG_ROOT / "subagents"
SKILLS_DIR = CLAWG_ROOT / "skills"
CRON_JOBS_FILE = CLAWG_HOME / "cron" / "jobs.json"


def _get_vault_root() -> Path | None:
    """Resolve the Second Brain vault root."""
    for env_key in ("CLAWG_SECOND_BRAIN_ROOT", "SECOND_BRAIN_ROOT"):
        val = os.getenv(env_key)
        if val:
            p = Path(val).expanduser()
            if p.is_dir():
                return p

    config_path = CLAWG_HOME / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                cfg = yaml.safe_load(f) or {}
            sb = cfg.get("second_brain", {})
            root = sb.get("root") or sb.get("vault_path")
            if root:
                p = Path(root).expanduser()
                if p.is_dir():
                    return p
        except Exception:
            pass

    for candidate in [
        Path.home() / ".openclaw" / "second-brain",
        Path.home() / "Documents" / "Second Brain OpenClaw - PROD",
        Path.home() / "Second Brain",
    ]:
        if candidate.is_dir():
            return candidate

    return None


# ─── Data Loaders ───

def _parse_agent_frontmatter(filepath: Path) -> dict[str, Any]:
    """Extract YAML frontmatter from an agent markdown file."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {"name": filepath.stem, "description": ""}

    front = match.group(1)
    data: dict[str, Any] = {}
    for line in front.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            data[key.strip()] = val.strip().strip('"').strip("'")

    return data


def load_agents() -> list[dict[str, Any]]:
    """Scan subagents/ directory for all agent profiles."""
    agents: list[dict[str, Any]] = []

    if not SUBAGENTS_DIR.is_dir():
        return agents

    for division_dir in sorted(SUBAGENTS_DIR.iterdir()):
        if not division_dir.is_dir():
            continue
        division = division_dir.name

        for md_file in sorted(division_dir.glob("*.md")):
            front = _parse_agent_frontmatter(md_file)
            name = front.get("name", md_file.stem)
            if name.startswith(f"{division}-"):
                name = name[len(division) + 1:]

            agents.append({
                "id": f"{division}/{md_file.stem}",
                "name": name,
                "division": division,
                "status": "idle",
                "model": front.get("model", "anthropic/claude-sonnet-4.6"),
                "description": front.get("description", ""),
                "emoji": front.get("emoji", ""),
                "color": front.get("color", ""),
                "sessions": 0,
                "lastActive": None,
            })

    return agents


def load_skills() -> list[dict[str, Any]]:
    """Scan skills/ directory for all skill definitions."""
    skills: list[dict[str, Any]] = []

    if not SKILLS_DIR.is_dir():
        return skills

    for category_dir in sorted(SKILLS_DIR.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name

        for skill_dir in sorted(category_dir.iterdir()):
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                # Try any .md file
                md_files = list(skill_dir.glob("*.md"))
                if md_files:
                    skill_md = md_files[0]
                else:
                    continue

            front = _parse_agent_frontmatter(skill_md)
            skills.append({
                "id": skill_dir.name,
                "name": front.get("name", skill_dir.name),
                "category": category,
                "description": front.get("description", ""),
                "version": front.get("version", "1.0.0"),
            })

    # Also scan flat .md files directly in skills/
    for md_file in sorted(SKILLS_DIR.glob("*.md")):
        if md_file.name == "INDEX.md":
            continue
        front = _parse_agent_frontmatter(md_file)
        skills.append({
            "id": md_file.stem,
            "name": front.get("name", md_file.stem),
            "category": "general",
            "description": front.get("description", ""),
            "version": front.get("version", "1.0.0"),
        })

    return skills


def load_crons() -> list[dict[str, Any]]:
    """Load cron jobs from ~/.clawg/cron/jobs.json."""
    if not CRON_JOBS_FILE.exists():
        return []

    try:
        data = json.loads(CRON_JOBS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "jobs" in data:
            return data["jobs"]
        return []
    except Exception:
        return []


def load_projects() -> list[dict[str, Any]]:
    """Discover projects from the vault and common paths."""
    projects: list[dict[str, Any]] = []

    vault = _get_vault_root()
    if vault:
        projects_dir = vault / "Projects"
        if projects_dir.is_dir():
            for item in sorted(projects_dir.iterdir()):
                if item.is_dir():
                    md_count = len(list(item.rglob("*.md")))
                    projects.append({
                        "name": item.name,
                        "path": str(item),
                        "lastModified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                        "files": md_count,
                    })

    # Always include the CLAWG project itself
    projects.insert(0, {
        "name": "CLAWG Core",
        "path": str(CLAWG_ROOT),
        "lastModified": datetime.now().isoformat(),
        "files": len(list(CLAWG_ROOT.glob("**/*.py"))),
    })

    return projects


def load_tasks() -> list[dict[str, Any]]:
    """Load tasks from vault or session state."""
    vault = _get_vault_root()
    tasks: list[dict[str, Any]] = []

    if vault:
        # Check for a tasks.md or todo.md in the vault
        for name in ("tasks.md", "todo.md", "TODO.md"):
            task_file = vault / name
            if task_file.exists():
                text = task_file.read_text(encoding="utf-8", errors="replace")
                for line in text.split("\n"):
                    line = line.strip()
                    if line.startswith("- [ ] "):
                        tasks.append({
                            "id": f"t-{len(tasks)+1}",
                            "name": line[6:].strip(),
                            "agent": "unassigned",
                            "status": "pending",
                            "priority": "medium",
                            "created": datetime.now().isoformat(),
                        })
                    elif line.startswith("- [x] "):
                        tasks.append({
                            "id": f"t-{len(tasks)+1}",
                            "name": line[6:].strip(),
                            "agent": "unassigned",
                            "status": "done",
                            "priority": "medium",
                            "created": datetime.now().isoformat(),
                        })

    return tasks


def load_config() -> dict[str, Any]:
    """Load CLAWG configuration."""
    config: dict[str, Any] = {
        "model": "anthropic/claude-sonnet-4.6",
        "vault_path": str(_get_vault_root() or "Not configured"),
        "skin": "default",
        "clawg_home": str(CLAWG_HOME),
    }

    config_path = CLAWG_HOME / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                cfg = yaml.safe_load(f) or {}
            model_cfg = cfg.get("model", {})
            if isinstance(model_cfg, dict):
                config["model"] = model_cfg.get("default", config["model"])
            display = cfg.get("display", {})
            if isinstance(display, dict):
                config["skin"] = display.get("skin", "default")
        except Exception:
            pass

    return config


# ─── HTTP Handler ───

class DashboardHandler(SimpleHTTPRequestHandler):
    """Serves the dashboard HTML and JSON API endpoints."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        # API routes
        if path.startswith("/api/"):
            self._handle_api(path, parsed.query)
            return

        # Default to command-center.html
        if path == "/" or path == "":
            self.path = "/command-center.html"

        super().do_GET()

    def _handle_api(self, path: str, query: str) -> None:
        params = parse_qs(query)

        routes: dict[str, Any] = {
            "/api/status": lambda: {"status": "ok", "version": "0.3.0", "timestamp": datetime.now().isoformat()},
            "/api/agents": load_agents,
            "/api/skills": load_skills,
            "/api/crons": load_crons,
            "/api/tasks": load_tasks,
            "/api/projects": load_projects,
            "/api/config": load_config,
        }

        handler = routes.get(path)
        if handler:
            try:
                data = handler()
                self._json_response(200, data)
            except Exception as e:
                logger.exception("API error: %s", path)
                self._json_response(500, {"error": str(e)})
        else:
            self._json_response(404, {"error": f"Unknown endpoint: {path}"})

    def _json_response(self, code: int, data: Any) -> None:
        body = json.dumps(data, default=str, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy request logs
        pass


# ─── Entry Point ───

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="CLAWG Command Center Server")
    parser.add_argument("--port", type=int, default=9777, help="Port to serve on (default: 9777)")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open browser")
    args = parser.parse_args()

    server = HTTPServer(("127.0.0.1", args.port), DashboardHandler)
    url = f"http://localhost:{args.port}"

    print(f"\n  \033[1;35mCLAWG Command Center\033[0m")
    print(f"  Serving at: \033[1;36m{url}\033[0m")
    print(f"  Dashboard:  \033[1;36m{DASHBOARD_DIR / 'command-center.html'}\033[0m")
    print(f"  Press Ctrl+C to stop\n")

    if not args.no_open:
        import webbrowser
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
