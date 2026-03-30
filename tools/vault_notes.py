"""
Vault Notes — Write to learning/ and Projects/ directories in the Second Brain.

Provides tools for agents to persist durable learnings and project notes
directly into the vault, making them visible to all agents via the
Shared Libraries Index in the system prompt.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clawg_cli.paths import (
    get_second_brain_learning_dir,
    get_second_brain_projects_dir,
    get_second_brain_root,
)
from tools.registry import registry

logger = logging.getLogger(__name__)


def _sanitize_filename(name: str) -> str:
    """Convert a title to a safe filename."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
    slug = slug.strip("-")[:80]
    return slug or "untitled"


def _resolve_dir(dir_type: str) -> Path | None:
    """Resolve vault directory by type."""
    if dir_type == "learning":
        d = get_second_brain_learning_dir()
    elif dir_type == "project":
        d = get_second_brain_projects_dir()
    else:
        return None

    if d:
        d.mkdir(parents=True, exist_ok=True)
        return d

    # Fallback to vault root + dir name
    root = get_second_brain_root()
    if root:
        fallback = root / dir_type
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    return None


def save_learning(title: str, content: str, tags: str = "") -> dict[str, str]:
    """Save a durable learning/lesson to the vault's learning/ directory."""
    learning_dir = _resolve_dir("learning")
    if not learning_dir:
        return {"error": "No Second Brain vault configured. Run: clawg second-brain link --path <vault>"}

    slug = _sanitize_filename(title)
    filepath = learning_dir / f"{slug}.md"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tag_line = f"tags: {tags}" if tags else ""

    md = f"""---
title: {title}
date: {now}
{tag_line}
---

# {title}

{content.strip()}
"""

    filepath.write_text(md, encoding="utf-8")
    return {
        "status": "ok",
        "message": f"Learning saved to learning/{slug}.md",
        "path": str(filepath),
    }


def save_project_note(project: str, title: str, content: str) -> dict[str, str]:
    """Save a project note to the vault's Projects/<project>/ directory."""
    projects_dir = _resolve_dir("project")
    if not projects_dir:
        return {"error": "No Second Brain vault configured. Run: clawg second-brain link --path <vault>"}

    project_slug = _sanitize_filename(project)
    project_dir = projects_dir / project_slug
    project_dir.mkdir(parents=True, exist_ok=True)

    note_slug = _sanitize_filename(title)
    filepath = project_dir / f"{note_slug}.md"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    md = f"""---
project: {project}
title: {title}
date: {now}
---

# {title}

{content.strip()}
"""

    filepath.write_text(md, encoding="utf-8")
    return {
        "status": "ok",
        "message": f"Note saved to Projects/{project_slug}/{note_slug}.md",
        "path": str(filepath),
    }


def list_learnings() -> list[dict[str, str]]:
    """List all files in the vault's learning/ directory."""
    learning_dir = _resolve_dir("learning")
    if not learning_dir or not learning_dir.exists():
        return []
    return [
        {"name": f.stem, "path": str(f), "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()}
        for f in sorted(learning_dir.glob("*.md"))
    ]


def list_project_notes(project: str = "") -> list[dict[str, str]]:
    """List project notes. If project is given, list notes in that project."""
    projects_dir = _resolve_dir("project")
    if not projects_dir or not projects_dir.exists():
        return []

    if project:
        project_slug = _sanitize_filename(project)
        pdir = projects_dir / project_slug
        if not pdir.exists():
            return []
        return [
            {"name": f.stem, "project": project, "path": str(f)}
            for f in sorted(pdir.glob("*.md"))
        ]

    # List all projects
    return [
        {"name": d.name, "path": str(d), "notes": len(list(d.glob("*.md")))}
        for d in sorted(projects_dir.iterdir()) if d.is_dir()
    ]


# ─── Tool Registration ───

_SCHEMAS = {
    "vault_save_learning": {
        "name": "vault_save_learning",
        "description": (
            "Save a durable learning, lesson, or postmortem to the Second Brain vault's learning/ directory. "
            "Use after discovering something non-obvious: a bug root cause, a decision rationale, "
            "a workflow improvement, or a tool quirk worth remembering. "
            "Learnings are visible to ALL agents in subsequent sessions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short descriptive title (used as filename)"},
                "content": {"type": "string", "description": "The learning content in markdown"},
                "tags": {"type": "string", "description": "Comma-separated tags (e.g. 'debugging, python, api')"},
            },
            "required": ["title", "content"],
        },
    },
    "vault_save_project_note": {
        "name": "vault_save_project_note",
        "description": (
            "Save a project note to the Second Brain vault's Projects/ directory. "
            "Use for project status updates, architecture decisions, meeting notes, "
            "or any project-specific information that should persist across sessions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name (creates a subdirectory)"},
                "title": {"type": "string", "description": "Note title (used as filename)"},
                "content": {"type": "string", "description": "Note content in markdown"},
            },
            "required": ["project", "title", "content"],
        },
    },
    "vault_list_learnings": {
        "name": "vault_list_learnings",
        "description": "List all learnings stored in the Second Brain vault's learning/ directory.",
        "parameters": {"type": "object", "properties": {}},
    },
    "vault_list_projects": {
        "name": "vault_list_projects",
        "description": "List projects and notes in the Second Brain vault's Projects/ directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Optional: filter to a specific project"},
            },
        },
    },
}


def _handle_save_learning(args: dict, **kw: Any) -> str:
    return json.dumps(save_learning(args.get("title", ""), args.get("content", ""), args.get("tags", "")))


def _handle_save_project_note(args: dict, **kw: Any) -> str:
    return json.dumps(save_project_note(args.get("project", ""), args.get("title", ""), args.get("content", "")))


def _handle_list_learnings(args: dict, **kw: Any) -> str:
    return json.dumps(list_learnings(), default=str)


def _handle_list_projects(args: dict, **kw: Any) -> str:
    return json.dumps(list_project_notes(args.get("project", "")), default=str)


_HANDLERS = {
    "vault_save_learning": _handle_save_learning,
    "vault_save_project_note": _handle_save_project_note,
    "vault_list_learnings": _handle_list_learnings,
    "vault_list_projects": _handle_list_projects,
}

for name, schema in _SCHEMAS.items():
    registry.register(
        name=name,
        toolset="vault_notes",
        schema=schema,
        handler=_HANDLERS[name],
        description=schema["description"],
        emoji="📝",
    )
