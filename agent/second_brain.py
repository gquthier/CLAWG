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

from clawg_cli.paths import (
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
        from clawg_cli.config import load_config

        cfg = load_config()
        return cfg if isinstance(cfg, dict) else {}
    except Exception as e:
        logger.warning("Could not load config for Second Brain: %s", e)
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


_SECRET_PATTERNS = re.compile(
    r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)", re.IGNORECASE
)

_SERVICE_LABELS = {
    "OPENAI_API_KEY": "OpenAI",
    "ANTHROPIC_API_KEY": "Anthropic",
    "OPENROUTER_API_KEY": "OpenRouter",
    "GOOGLE_API_KEY": "Google",
    "ELEVENLABS_API_KEY": "ElevenLabs",
    "FIRECRAWL_API_KEY": "Firecrawl",
    "TAVILY_API_KEY": "Tavily",
    "BROWSERBASE_API_KEY": "Browserbase",
    "TELEGRAM_BOT_TOKEN": "Telegram Bot",
    "DISCORD_BOT_TOKEN": "Discord Bot",
    "SLACK_BOT_TOKEN": "Slack Bot",
    "GITHUB_TOKEN": "GitHub",
    "HASS_TOKEN": "Home Assistant",
    "TWILIO_ACCOUNT_SID": "Twilio",
    "WANDB_API_KEY": "Weights & Biases",
    "REPLICATE_API_TOKEN": "Replicate",
    "NOUS_API_KEY": "Nous Research",
    "DEEPSEEK_API_KEY": "DeepSeek",
    "MISTRAL_API_KEY": "Mistral",
    "SUPABASE_KEY": "Supabase",
    "STRIPE_SECRET_KEY": "Stripe",
    "RESEND_API_KEY": "Resend",
}


def _build_env_summary() -> str:
    """Build a summary of configured env vars and vault keystore keys.

    Lists NAMES ONLY (never values) so the agent knows which services are
    available. Groups by category for readability.
    """
    lines: list[str] = []

    # System env vars to exclude (not user-configured secrets)
    _system_vars = frozenset({
        "SSH_AUTH_SOCK", "SSH_AGENT_PID", "GPG_AGENT_INFO",
        "SECURITYSESSIONID", "TOKENFILE", "CREDENTIAL_HELPER",
    })

    # 1. Scan env vars for configured secrets
    env_configured: list[str] = []
    for key in sorted(os.environ):
        if key in _system_vars:
            continue
        if not _SECRET_PATTERNS.search(key):
            continue
        val = os.environ.get(key, "").strip()
        if not val or len(val) < 4:
            continue
        # Skip vars that look auto-set (paths, pids, etc.)
        if val.startswith("/") or val.isdigit():
            continue
        label = _SERVICE_LABELS.get(key, "")
        entry = f"`{key}`"
        if label:
            entry += f" ({label})"
        env_configured.append(entry)

    # 2. Scan vault keystore catalog (names only)
    vault_keys: list[str] = []
    try:
        from tools.vault_keystore import list_keys
        for k in list_keys():
            name = k.get("name", "")
            svc = k.get("service", "")
            entry = f"`{name}`"
            if svc:
                entry += f" ({svc})"
            if entry not in env_configured:
                vault_keys.append(entry)
    except Exception:
        pass

    if not env_configured and not vault_keys:
        return ""

    lines.append("## Available Services & Credentials")
    lines.append("")
    lines.append("Configured API keys and tokens (names only, values are secret):")
    lines.append("")

    if env_configured:
        lines.append("**From environment (.env):**")
        for entry in env_configured:
            lines.append(f"- {entry}")

    if vault_keys:
        if env_configured:
            lines.append("")
        lines.append("**From vault keystore (encrypted):**")
        for entry in vault_keys:
            lines.append(f"- {entry}")

    lines.append("")
    lines.append("Use `vault_keystore_get` to retrieve any key. Never display values in chat.")

    return "\n".join(lines)


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
            ("Agents", ("AGENTS.md", "agents.md")),
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

    # ── Available Services (env vars configured — names only, never values) ──
    env_block = _build_env_summary()
    if env_block:
        sections.append(env_block)

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
