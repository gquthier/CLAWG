"""Second Brain prompt assembly for CLAWG.

This module loads shared markdown context from an Obsidian-compatible vault and
builds a compact system-prompt block used by all agents/subagents.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Iterable, Optional

from hermes_cli.paths import (
    get_second_brain_root,
    get_second_brain_memory_dir,
    get_second_brain_skills_dir,
    get_second_brain_subagents_dir,
    get_second_brain_tools_dir,
    get_second_brain_learning_dir,
    get_second_brain_projects_dir,
    get_second_brain_agent_dir,
    sanitize_agent_id,
)

logger = logging.getLogger(__name__)


_CONTEXT_THREAT_PATTERNS = [
    (r"ignore\\s+(previous|all|above|prior)\\s+instructions", "prompt_injection"),
    (r"do\\s+not\\s+tell\\s+the\\s+user", "deception_hide"),
    (r"system\\s+prompt\\s+override", "sys_prompt_override"),
    (r"disregard\\s+(your|all|any)\\s+(instructions|rules|guidelines)", "disregard_rules"),
    (r"curl\\s+[^\\n]*\\$\\{?\\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)", "exfil_curl"),
    (r"cat\\s+[^\\n]*(\\.env|credentials|\\.netrc|\\.pgpass)", "read_secrets"),
]

_CONTEXT_INVISIBLE_CHARS = {
    "\u200b", "\u200c", "\u200d", "\u2060", "\ufeff",
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
}

_MAX_FILE_CHARS = 12_000
_MAX_INDEX_ITEMS = 60


def _load_config_safe() -> dict:
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        return cfg if isinstance(cfg, dict) else {}
    except Exception as e:
        logger.debug("Could not load config for Second Brain: %s", e)
        return {}


def _truncate(content: str, label: str, max_chars: int = _MAX_FILE_CHARS) -> str:
    if len(content) <= max_chars:
        return content
    head = int(max_chars * 0.75)
    tail = int(max_chars * 0.15)
    marker = (
        f"\n\n[...truncated {label}: kept {head}+{tail} of {len(content)} chars. "
        "Use file tools to inspect the full file.]\n\n"
    )
    return content[:head] + marker + content[-tail:]


def _scan_content(content: str, label: str) -> str:
    findings = []
    for char in _CONTEXT_INVISIBLE_CHARS:
        if char in content:
            findings.append(f"invisible_unicode_U+{ord(char):04X}")

    for pattern, tag in _CONTEXT_THREAT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(tag)

    if findings:
        logger.warning("Second Brain file blocked (%s): %s", label, ", ".join(findings))
        return f"[BLOCKED: {label} contained risky content ({', '.join(findings)}).]"
    return content


def _read_md(path: Path, label: str) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.debug("Could not read %s: %s", path, e)
        return None

    if not raw:
        return None
    safe = _scan_content(raw, label)
    return _truncate(safe, label)


def _first_existing(root: Path, candidates: Iterable[str]) -> Optional[Path]:
    for rel in candidates:
        p = root / rel
        if p.exists() and p.is_file():
            return p
    return None


def _list_entries(path: Optional[Path], *, max_items: int = _MAX_INDEX_ITEMS) -> str:
    if not path or not path.exists() or not path.is_dir():
        return "(not found)"
    items: list[str] = []
    try:
        for entry in sorted(path.iterdir(), key=lambda p: p.name.lower()):
            if entry.name.startswith("."):
                continue
            name = entry.name + ("/" if entry.is_dir() else "")
            items.append(name)
            if len(items) >= max_items:
                break
    except Exception as e:
        logger.debug("Could not list %s: %s", path, e)
        return "(unavailable)"

    if not items:
        return "(empty)"
    if len(items) == max_items:
        items.append("...")
    return ", ".join(items)


def resolve_active_agent_id(agent_id: str | None = None, config: dict | None = None) -> str:
    cfg = config or _load_config_safe()
    if agent_id and str(agent_id).strip():
        return sanitize_agent_id(agent_id)
    default_id = ((cfg.get("second_brain") or {}).get("agent_default_id") or "default")
    return sanitize_agent_id(str(default_id))


def build_second_brain_prompt(agent_id: str | None = None, cwd: str | None = None) -> str:
    """Build a shared Second Brain context block for system prompt injection."""
    _ = cwd  # reserved for future cwd-scoped loading
    cfg = _load_config_safe()
    root = get_second_brain_root(config=cfg, must_exist=True)
    if not root:
        return ""

    resolved_agent_id = resolve_active_agent_id(agent_id=agent_id, config=cfg)
    agent_dir = get_second_brain_agent_dir(resolved_agent_id, config=cfg)

    sections: list[str] = []

    master_files = [
        ("Master User", _first_existing(root, ("user.md", "User.md"))),
        (
            "Master Environment",
            _first_existing(root, ("environment.md", "environnement.md", "Environment.md", "ENVIRONNEMENT.md")),
        ),
        ("Master Philosophy", _first_existing(root, ("philosophy.md", "Philosophy.md"))),
        ("Master API", _first_existing(root, ("api.md", "API.md"))),
    ]

    master_blocks: list[str] = []
    for label, path in master_files:
        if not path:
            continue
        content = _read_md(path, f"{label} ({path.name})")
        if content:
            master_blocks.append(f"### {label} ({path.name})\n\n{content}")

    if master_blocks:
        sections.append("## Master Files\n\n" + "\n\n".join(master_blocks))

    agent_blocks: list[str] = []
    if agent_dir and agent_dir.exists():
        per_agent_candidates = [
            ("Identity", ("identity.md", "IDENTITY.md")),
            ("Adjoint", ("adjoint.md", "ADJOINT.md")),
            ("Soul", ("soul.md", "SOUL.md")),
            ("User Overlay", ("user.md", "USER.md")),
            ("Environment Overlay", ("environment.md", "environnement.md", "ENVIRONMENT.md", "ENVIRONNEMENT.md")),
        ]
        for label, names in per_agent_candidates:
            path = _first_existing(agent_dir, names)
            if not path:
                continue
            content = _read_md(path, f"Agent {resolved_agent_id} {label}")
            if content:
                agent_blocks.append(f"### {label} ({path.name})\n\n{content}")

    if agent_blocks:
        sections.append(
            f"## Agent Profile ({resolved_agent_id})\n\n"
            + "\n\n".join(agent_blocks)
        )

    skills_dir = get_second_brain_skills_dir(config=cfg)
    subagents_dir = get_second_brain_subagents_dir(config=cfg)
    tools_dir = get_second_brain_tools_dir(config=cfg)
    memory_dir = get_second_brain_memory_dir(config=cfg)
    learning_dir = get_second_brain_learning_dir(config=cfg)
    projects_dir = get_second_brain_projects_dir(config=cfg)

    index_block = (
        "## Shared Libraries Index\n"
        f"- skills/: {_list_entries(skills_dir)}\n"
        f"- subagent/: {_list_entries(subagents_dir)}\n"
        f"- tools/: {_list_entries(tools_dir)}\n"
        f"- learning/: {_list_entries(learning_dir)}\n"
        f"- Projects/: {_list_entries(projects_dir)}\n"
        f"- Large Memory/: {_list_entries(memory_dir)}"
    )
    sections.append(index_block)

    policy_block = (
        "## Execution Policy\n"
        "Second Brain is the shared source of truth across all agents.\n"
        "Before executing complex tasks: check relevant master files, then inspect\n"
        "skills and subagents in this vault. Reuse existing procedures whenever possible.\n"
        "Persist durable knowledge back into this vault structure, not into private\n"
        "agent-local files outside the shared Second Brain.\n"
    )
    sections.append(policy_block)

    return (
        "# Second Brain Context\n"
        f"Root: {root}\n"
        f"Active agent profile: {resolved_agent_id}\n\n"
        + "\n\n".join(sections)
    )
