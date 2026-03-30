"""Path resolution helpers for CLAWG runtime and Second Brain integration.

This module centralizes path selection so every runtime component resolves:
- the app home directory (CLAWG_HOME with CLAWG_HOME backward compatibility)
- the shared Second Brain vault root
- shared storage locations (memory, skills, subagents, tools)
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional


CLAWG_HOME_ENV = "CLAWG_HOME"
LEGACY_HOME_ENV = "CLAWG_HOME"

CLAWG_SECOND_BRAIN_ENV = "CLAWG_SECOND_BRAIN_ROOT"
LEGACY_SECOND_BRAIN_ENV = "SECOND_BRAIN_ROOT"

DEFAULT_CLAWG_HOME = Path.home() / ".clawg"
DEFAULT_LEGACY_HOME = Path.home() / ".clawg"

DEFAULT_SECOND_BRAIN_CANDIDATES = (
    Path.home() / ".openclaw" / "second-brain",
    Path.home() / "Documents" / "Second Brain OpenClaw - PROD",
)


def _normalized(path_like: str | os.PathLike[str]) -> Path:
    """Return an expanded, normalized path without requiring existence."""
    p = Path(path_like).expanduser()
    try:
        # strict=False keeps behavior for paths that do not exist yet.
        return p.resolve(strict=False)
    except OSError:
        return p


def get_runtime_home() -> Path:
    """Return the active CLAWG home directory.

    Precedence:
    1) CLAWG_HOME env var
    2) CLAWG_HOME env var (backward compatibility)
    3) ~/.clawg when present
    4) ~/.clawg when present
    5) ~/.clawg default
    """
    clawg_env = os.getenv(CLAWG_HOME_ENV)
    if clawg_env:
        return _normalized(clawg_env)

    legacy_env = os.getenv(LEGACY_HOME_ENV)
    if legacy_env:
        return _normalized(legacy_env)

    if DEFAULT_CLAWG_HOME.exists():
        return DEFAULT_CLAWG_HOME
    if DEFAULT_LEGACY_HOME.exists():
        return DEFAULT_LEGACY_HOME
    return DEFAULT_CLAWG_HOME


def sync_home_env_vars(home: Path | None = None) -> Path:
    """Keep CLAWG_HOME and CLAWG_HOME aligned for runtime compatibility."""
    if home is None:
        home = get_runtime_home()
    home = _normalized(home)

    clawg_env = os.getenv(CLAWG_HOME_ENV)
    legacy_env = os.getenv(LEGACY_HOME_ENV)

    if clawg_env and legacy_env:
        # Prefer CLAWG_HOME when both are set but disagree.
        if _normalized(clawg_env) != _normalized(legacy_env):
            os.environ[LEGACY_HOME_ENV] = str(_normalized(clawg_env))
            return _normalized(clawg_env)
        return _normalized(clawg_env)

    os.environ.setdefault(CLAWG_HOME_ENV, str(home))
    os.environ.setdefault(LEGACY_HOME_ENV, str(home))
    return home


def _read_second_brain_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, dict):
        return {}
    section = config.get("second_brain")
    return section if isinstance(section, dict) else {}


def is_second_brain_enabled(config: dict[str, Any] | None = None) -> bool:
    section = _read_second_brain_config(config)
    enabled = section.get("enabled", True)
    return bool(enabled)


def _coerce_optional_path(value: Any) -> Optional[Path]:
    if value is None:
        return None
    if isinstance(value, Path):
        return _normalized(value)
    text = str(value).strip()
    if not text:
        return None
    return _normalized(text)


def get_second_brain_root(
    config: dict[str, Any] | None = None,
    *,
    must_exist: bool = False,
) -> Optional[Path]:
    """Resolve the shared Second Brain root directory.

    Precedence:
    1) CLAWG_SECOND_BRAIN_ROOT env var
    2) SECOND_BRAIN_ROOT env var (legacy)
    3) config.second_brain.root
    4) discovered defaults (symlink + common vault location)
    """
    if not is_second_brain_enabled(config):
        return None

    candidates: list[Path] = []

    env_root = _coerce_optional_path(os.getenv(CLAWG_SECOND_BRAIN_ENV))
    if env_root:
        candidates.append(env_root)

    env_legacy = _coerce_optional_path(os.getenv(LEGACY_SECOND_BRAIN_ENV))
    if env_legacy:
        candidates.append(env_legacy)

    section = _read_second_brain_config(config)
    cfg_root = _coerce_optional_path(section.get("root"))
    if cfg_root:
        candidates.append(cfg_root)

    candidates.extend(DEFAULT_SECOND_BRAIN_CANDIDATES)

    seen: set[str] = set()
    deduped: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)

    for candidate in deduped:
        if candidate.exists():
            return _normalized(candidate)

    if must_exist:
        return None
    return deduped[0] if deduped else None


def _resolve_under_root(root: Path, value: Any, default_name: str) -> Path:
    if value is None:
        configured = Path(default_name)
    elif isinstance(value, Path):
        configured = value.expanduser()
    else:
        text = str(value).strip()
        configured = Path(text).expanduser() if text else Path(default_name)

    if configured.is_absolute():
        return _normalized(configured)
    return _normalized(root / configured)


def get_second_brain_memory_dir(config: dict[str, Any] | None = None) -> Optional[Path]:
    root = get_second_brain_root(config=config)
    if not root:
        return None

    section = _read_second_brain_config(config)
    configured = section.get("memory_dir")
    memory_dir = _resolve_under_root(root, configured, "Large Memory")

    # If configured/default path doesn't exist yet, accept common alternatives.
    if not memory_dir.exists():
        for alt_name in ("Large Memory", "large-memory", "memory", "memories"):
            alt = root / alt_name
            if alt.exists():
                return _normalized(alt)
    return memory_dir


def get_second_brain_skills_dir(config: dict[str, Any] | None = None) -> Optional[Path]:
    root = get_second_brain_root(config=config)
    if not root:
        return None
    section = _read_second_brain_config(config)
    skills_dir = _resolve_under_root(root, section.get("skills_dir"), "skills")
    if not skills_dir.exists():
        for alt_name in ("skills", "Skills"):
            alt = root / alt_name
            if alt.exists():
                return _normalized(alt)
    return skills_dir


def get_second_brain_subagents_dir(config: dict[str, Any] | None = None) -> Optional[Path]:
    root = get_second_brain_root(config=config)
    if not root:
        return None
    section = _read_second_brain_config(config)
    subagents_dir = _resolve_under_root(root, section.get("subagents_dir"), "subagent")
    if not subagents_dir.exists():
        for alt_name in ("subagent", "subagents", "sub-agents"):
            alt = root / alt_name
            if alt.exists():
                return _normalized(alt)
    return subagents_dir


def get_second_brain_tools_dir(config: dict[str, Any] | None = None) -> Optional[Path]:
    root = get_second_brain_root(config=config)
    if not root:
        return None
    section = _read_second_brain_config(config)
    tools_dir = _resolve_under_root(root, section.get("tools_dir"), "tools")
    if not tools_dir.exists():
        for alt_name in ("tools", "Tools"):
            alt = root / alt_name
            if alt.exists():
                return _normalized(alt)
    return tools_dir


def get_second_brain_learning_dir(config: dict[str, Any] | None = None) -> Optional[Path]:
    root = get_second_brain_root(config=config)
    if not root:
        return None
    section = _read_second_brain_config(config)
    learning_dir = _resolve_under_root(root, section.get("learning_dir"), "learning")
    if not learning_dir.exists():
        for alt_name in ("learning", "Learning"):
            alt = root / alt_name
            if alt.exists():
                return _normalized(alt)
    return learning_dir


def get_second_brain_projects_dir(config: dict[str, Any] | None = None) -> Optional[Path]:
    root = get_second_brain_root(config=config)
    if not root:
        return None
    section = _read_second_brain_config(config)
    projects_dir = _resolve_under_root(root, section.get("projects_dir"), "Projects")
    if not projects_dir.exists():
        for alt_name in ("Projects", "projects", "Projets", "projets"):
            alt = root / alt_name
            if alt.exists():
                return _normalized(alt)
    return projects_dir


def get_second_brain_agents_dir(config: dict[str, Any] | None = None) -> Optional[Path]:
    root = get_second_brain_root(config=config)
    if not root:
        return None
    section = _read_second_brain_config(config)
    agents_dir = _resolve_under_root(root, section.get("agent_profiles_dir"), "agents")
    if not agents_dir.exists():
        for alt_name in ("agents", "Agents"):
            alt = root / alt_name
            if alt.exists():
                return _normalized(alt)
    return agents_dir


def sanitize_agent_id(agent_id: str | None) -> str:
    """Normalize user-provided agent IDs for filesystem-safe directory names."""
    raw = (agent_id or "").strip().lower()
    if not raw:
        return "default"
    cleaned = re.sub(r"[^a-z0-9._-]+", "-", raw)
    cleaned = cleaned.strip("-._")
    return cleaned or "default"


def get_second_brain_agent_dir(
    agent_id: str | None,
    config: dict[str, Any] | None = None,
) -> Optional[Path]:
    agents_dir = get_second_brain_agents_dir(config=config)
    if not agents_dir:
        return None
    return _normalized(agents_dir / sanitize_agent_id(agent_id))


def get_shared_memory_dir(config: dict[str, Any] | None = None) -> Path:
    """Return the memory directory used by the runtime.

    Uses Second Brain when enabled and resolved, otherwise falls back to
    <home>/memories.
    """
    sb_memory = get_second_brain_memory_dir(config=config)
    if sb_memory:
        return sb_memory
    return get_runtime_home() / "memories"


def get_shared_skills_dir(config: dict[str, Any] | None = None) -> Path:
    """Return the skills directory used by the runtime."""
    sb_skills = get_second_brain_skills_dir(config=config)
    if sb_skills:
        return sb_skills
    return get_runtime_home() / "skills"


def bootstrap_second_brain(root: Path, agent_id: str = "default", force: bool = False) -> dict[str, list[Path]]:
    """Create a CLAWG-compatible Second Brain directory structure."""
    root = _normalized(root)
    aid = sanitize_agent_id(agent_id)

    created_dirs: list[Path] = []
    created_files: list[Path] = []

    dirs_to_create = [
        root,
        root / "Large Memory",
        root / "Projects",
        root / "learning",
        root / "skills",
        root / "subagent",
        root / "tools",
        root / "agents" / aid,
        root / "dashboard",
    ]

    for d in dirs_to_create:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created_dirs.append(d)

    file_templates = {
        root / "SECOND_BRAIN.md": "# CLAWG Second Brain\n\nThis vault is the shared source of truth for all CLAWG agents.\n\n",
        root / "user.md": "# User\n\nCore user profile and stable preferences shared across agents.\n",
        root / "environment.md": """# Environment

Machine, repo, paths, and runtime conventions.

## Obsidian Second Brain

This vault is the shared source of truth for all CLAWG agents. It is an Obsidian vault.

### Vault Structure

```
vault/
├── user.md              — User profile, preferences, constraints
├── environment.md       — This file. Machine topology, paths, conventions
├── philosophy.md        — Principles, non-negotiables, decision framework
├── api.md               — API schemas and auth expectations
├── agents/<id>/         — Per-agent profiles (identity, soul, AGENTS, overlays)
├── skills/              — Reusable execution playbooks (shared across agents)
├── subagent/            — Specialist agent definitions
├── tools/               — Global tool docs and contracts
├── learning/            — Durable lessons and postmortems
├── Projects/            — Ephemeral project notes
├── Large Memory/        — Large documents, reference material
└── dashboard/           — HTML dashboards (Command Center + per-project)
```

### How to Use This Vault

- **Read** any file for context: skills, agent profiles, project notes, learnings
- **Write** new learnings, project notes, and updates to keep the vault current
- **Create dashboards** in `dashboard/` for long-term projects (see skill: obsidian-dashboard)
- All agents share this vault — changes are immediately visible to every agent

### Dashboard System

The `dashboard/` folder contains interactive HTML dashboards viewable in Obsidian.

- **Command Center** (`dashboard/command-center.html`): Global overview of all agents, skills, crons, tasks, and projects with 3D visualization
- **Project Dashboards** (`dashboard/<project-name>.html`): Per-project tracking dashboards

**Obsidian Plugin Required**: Install **Custom Frames** or **HTML Reader** in Obsidian to view dashboards.
Recommended: `obsidian-custom-frames` by Ellpeck — turns HTML files into panes.

To embed a dashboard in a note:
```markdown
```embedhtml
path: dashboard/my-project.html
height: 800
`` `
```

Or use an iframe:
```html
<iframe src="dashboard/my-project.html" width="100%" height="800" style="border:none;"></iframe>
```

### When to Propose a Dashboard

Agents should propose creating a project dashboard when:
- A project spans more than 2 weeks of active work
- There are multiple agents collaborating on the same project
- The user needs visibility into progress, milestones, or metrics
- The project has recurring tasks, cron jobs, or scheduled deliverables

Use the `obsidian-dashboard` skill (in `skills/note-taking/obsidian-dashboard/`) to create dashboards.
""",
        root / "philosophy.md": "# Philosophy\n\nProject principles, coding standards, and decision rules.\n",
        root / "api.md": "# API\n\nGlobal endpoints, credentials mapping, and integration notes.\n",
        root / "dashboard" / "README.md": """# Dashboards

Interactive HTML dashboards for CLAWG projects.

## Files

- **command-center.html** — Global Command Center with 3D agent visualization
- **project-template.html** — Template for creating new project dashboards
- **<project-name>.html** — Per-project dashboards (created by agents)

## How to View

### Option 1: CLAWG Server (recommended)
```bash
clawg dashboard
```
Opens all dashboards in your browser with live data.

### Option 2: Obsidian Plugin
Install one of these Community Plugins in Obsidian:
- **HTML Reader** (`obsidian-html-plugin`) — click any `.html` file to view as a tab
- **Custom Frames** (`obsidian-custom-frames`) — embed as panes

### Option 3: Embed in a Note
```html
<iframe src="dashboard/command-center.html" width="100%" height="900" style="border:none;"></iframe>
```

## Creating a New Dashboard

Agents can create project dashboards using the `obsidian-dashboard` skill.
Or duplicate `project-template.html`, rename it, and edit the configuration section at the top.
""",
        root / "Large Memory" / "MEMORY.md": "",
        root / "Large Memory" / "USER.md": "",
        root / "agents" / aid / "identity.md": "# Identity\n\nWho this agent is and what it owns.\n",
        root / "agents" / aid / "AGENTS.md": "# Agents\n\nHow this agent coordinates with other agents and subagents.\n",
        root / "agents" / aid / "soul.md": "# Soul\n\nVoice, style, behavior constraints, and reasoning posture.\n",
        root / "agents" / aid / "user.md": "# User Overlay\n\nAgent-specific user preferences.\n",
        root / "agents" / aid / "environment.md": """# Environment Overlay

Agent-specific workspace assumptions.

## Second Brain Access

You have full read/write access to this Obsidian vault. Key capabilities:

1. **Read context**: Load any file from the vault for background knowledge
2. **Write learnings**: Save durable lessons to `learning/` after notable sessions
3. **Update project notes**: Keep `Projects/` current with latest status
4. **Create dashboards**: Use the `obsidian-dashboard` skill to build HTML dashboards in `dashboard/`

## Dashboard Capability

You can create interactive HTML dashboards for long-term projects. These are saved to `dashboard/<project>.html` and viewable in Obsidian.

**When to propose a dashboard:**
- Project has been active for 2+ weeks
- Multiple milestones or phases to track
- User would benefit from visual progress tracking
- Project has metrics, KPIs, or recurring deliverables

**How to create one:**
Use the `obsidian-dashboard` skill, or generate an HTML file in `dashboard/` following the project dashboard template.

A dashboard should include: project overview, milestone tracker, task status, metrics/KPIs, and a timeline of key events.
""",
    }

    for path, content in file_templates.items():
        if force or not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            created_files.append(path)

    # Copy dashboard files if available
    import shutil
    dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
    for html_name in ("command-center.html", "project-template.html"):
        src = dashboard_dir / html_name
        dst = root / "dashboard" / html_name
        if src.exists() and (force or not dst.exists()):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            created_files.append(dst)

    return {"dirs": created_dirs, "files": created_files}
