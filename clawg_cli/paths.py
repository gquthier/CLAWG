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


def _get_default_soul() -> str:
    """Load the default soul template for new agents."""
    try:
        from clawg_cli.default_soul import DEFAULT_SOUL_MD
        return DEFAULT_SOUL_MD
    except Exception:
        return "# Soul\n\nVoice, style, behavior constraints, and reasoning posture.\n"


CLAWG_HOME_ENV = "CLAWG_HOME"
LEGACY_HOME_ENV = "CLAWG_HOME"

CLAWG_SECOND_BRAIN_ENV = "CLAWG_SECOND_BRAIN_ROOT"
LEGACY_SECOND_BRAIN_ENV = "SECOND_BRAIN_ROOT"

DEFAULT_CLAWG_HOME = Path.home() / ".clawg"
DEFAULT_LEGACY_HOME = Path.home() / ".clawg"

DEFAULT_SECOND_BRAIN_CANDIDATES = (
    Path.home() / ".clawg" / "second-brain",
    Path.home() / "Second Brain",
    Path.home() / "Documents" / "Second Brain",
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
        root / "secrets",
    ]

    for d in dirs_to_create:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created_dirs.append(d)

    file_templates = {
        root / "SECOND_BRAIN.md": "# CLAWG Second Brain\n\nAutonomous open-source AI agents with a portable brain.\n\n",
        root / "user.md": "# User\n\nCore user profile and stable preferences shared across agents.\n",
        root / "environment.md": """# Environment

## Who You Are

You are a CLAWG agent — an autonomous AI agent operating natively inside a Second Brain.
This Second Brain is an Obsidian vault: a folder of markdown files that contains everything
your user knows, wants, and has built. It is your long-term memory, your skill library,
and your shared context with every other agent in this system.

You MUST read and use this vault. It is not optional documentation — it is your operating context.
Every file listed below was written for you. Read `user.md` to know who your user is.
Read `philosophy.md` to know their rules. Read `api.md` to know what services are available.
The more you use this vault, the more useful you become.

## Vault Paths

| Path | What it is | How to use it |
|------|-----------|---------------|
| `user.md` | User profile, preferences, constraints | Read at session start to personalize your behavior |
| `philosophy.md` | Principles, non-negotiables, decision rules | Follow these rules in every decision |
| `api.md` | API endpoints, encrypted keystore docs | Check before making external calls |
| `agents/<id>/` | Your identity, personality, delegation rules | This defines who YOU are |
| `skills/` | 33+ shared skills with step-by-step procedures | `skills_list` then `skill_view` before reinventing |
| `subagent/` | 150+ specialist agent profiles | Read before delegating — pick the right expert |
| `learning/` | Durable lessons from past sessions | Read before starting complex tasks. Write with `vault_save_learning` |
| `Projects/` | Per-project notes and status | Write with `vault_save_project_note`. Check before asking the user for context they already gave |
| `Large Memory/` | MEMORY.md + USER.md (persistent memory) | Managed by `memory` tool. Updated automatically |
| `secrets/` | AES-encrypted API keys | `vault_keystore_get` to retrieve. `vault_keystore_save` to store. NEVER display values |
| `dashboard/` | HTML dashboards viewable in Obsidian | Propose via `obsidian-dashboard` skill for long-term projects |

## Mandatory Behaviors

1. **User sends an API key or token** → call `vault_keystore_save` immediately. NEVER echo the value back.
2. **You need a service key** → `vault_keystore_list` first, then `vault_keystore_get`. Do not ask the user if the key exists.
3. **You learn something non-obvious** → `vault_save_learning` so future agents benefit.
4. **Project active 2+ weeks** → propose a dashboard via `obsidian-dashboard` skill.
5. **Before starting complex work** → check `learning/` and `skills/` for existing procedures.
6. **All changes you make are instantly shared** with every other agent in this vault.
""",
        root / "philosophy.md": "# Philosophy\n\nProject principles, coding standards, and decision rules.\n",
        root / "api.md": """# API

Endpoints, credentials, and integration notes.

## Keystore

Encrypted secrets in `secrets/keystore.enc`. Catalog (names only) at `secrets/catalog.md`.
Master key: `~/.clawg/.keystore-key` (auto-generated). Also exports to `~/.clawg/.env`.

Tools: `vault_keystore_save`, `vault_keystore_get`, `vault_keystore_list`, `vault_keystore_delete`
Rule: NEVER display secret values. Detect key patterns (sk-..., ghp_..., xoxb-...) and offer to save.
""",
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
        root / "Dashboard.md": """# Dashboard

Open the CLAWG Command Center directly in Obsidian.

## Quick Setup (one time)

1. Open Obsidian Settings → Community Plugins → Browse
2. Search for **"HTML Reader"** (by nuthrash)
3. Install and enable it
4. Click on `dashboard/command-center.html` in the file explorer → it opens as a tab

That's it. The dashboard shows all your agents, skills, crons, and projects.

## Alternative: Browser

```bash
clawg dashboard
```

Opens the Command Center in your browser at http://localhost:9777 with live data from your vault.

## Files

- `dashboard/command-center.html` → 3D visualization of agents, skills, projects, crons
- `dashboard/project-template.html` → Template for per-project dashboards
""",
        root / "Large Memory" / "MEMORY.md": "",
        root / "Large Memory" / "USER.md": "",
        root / "agents" / aid / "identity.md": f"""# Identity

You are **{aid}**, a CLAWG agent operating inside a shared Second Brain vault.
You are autonomous, persistent, and collaborative. You share this vault with other agents.

Your capabilities:
- Full terminal access (bash/zsh)
- File read/write across the system
- Web search and content extraction
- Browser automation
- Image analysis and generation
- Text-to-speech
- Delegation to 150+ specialist subagents
- Encrypted API key management
- Persistent memory across sessions
- Skill execution (5,200+ available skills)
- Cron job scheduling
- Multi-platform messaging (Telegram, Discord, Slack, etc.)
""",
        root / "agents" / aid / "AGENTS.md": """# Agents

You can delegate tasks to specialist subagents in `subagent/`. Before delegating:
1. Check `subagent/` for the right expert (150+ profiles across 14 divisions)
2. Pick the agent whose role matches the task
3. Provide clear context and success criteria

Divisions: engineering, design, marketing, paid-media, sales, product,
project-management, testing, support, spatial-computing, specialized,
academic, game-development, strategy.
""",
        root / "agents" / aid / "soul.md": _get_default_soul(),
        root / "agents" / aid / "user.md": "# User Overlay\n\nAgent-specific user preferences.\n",
        root / "agents" / aid / "environment.md": """# Environment Overlay

Full vault access. See master `environment.md` for paths.

Vault tools: `vault_keystore_*`, `vault_save_learning`, `vault_save_project_note`, `memory`, `skills_list`
Dashboard skill: `obsidian-dashboard` — propose for projects active 2+ weeks.
""",
    }

    for path, content in file_templates.items():
        if force or not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            created_files.append(path)

    import shutil
    repo_root = Path(__file__).resolve().parent.parent

    # Copy dashboard files if available
    dashboard_dir = repo_root / "dashboard"
    for html_name in ("command-center.html", "project-template.html"):
        src = dashboard_dir / html_name
        dst = root / "dashboard" / html_name
        if src.exists() and (force or not dst.exists()):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            created_files.append(dst)

    # Copy bundled skills into vault
    repo_skills = repo_root / "skills"
    vault_skills = root / "skills"
    if repo_skills.is_dir():
        for skill_src in repo_skills.rglob("SKILL.md"):
            rel = skill_src.relative_to(repo_skills)
            skill_dst = vault_skills / rel
            if force or not skill_dst.exists():
                skill_dst.parent.mkdir(parents=True, exist_ok=True)
                # Copy the entire skill directory (SKILL.md + any templates/scripts)
                skill_dir_src = skill_src.parent
                skill_dir_dst = skill_dst.parent
                for f in skill_dir_src.rglob("*"):
                    if f.is_file():
                        dst = skill_dir_dst / f.relative_to(skill_dir_src)
                        if force or not dst.exists():
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(f, dst)
                            created_files.append(dst)

    # Copy bundled subagents into vault
    repo_subagents = repo_root / "subagents"
    vault_subagents = root / "subagent"
    if repo_subagents.is_dir():
        for md_src in repo_subagents.rglob("*.md"):
            rel = md_src.relative_to(repo_subagents)
            md_dst = vault_subagents / rel
            if force or not md_dst.exists():
                md_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(md_src, md_dst)
                created_files.append(md_dst)

    return {"dirs": created_dirs, "files": created_files}
