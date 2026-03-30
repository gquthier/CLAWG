"""CLI commands for CLAWG Second Brain integration."""

from __future__ import annotations

import os
from pathlib import Path

from clawg_cli.config import load_config, save_config
from clawg_cli.paths import (
    CLAWG_SECOND_BRAIN_ENV,
    LEGACY_SECOND_BRAIN_ENV,
    bootstrap_second_brain,
    get_second_brain_root,
    get_second_brain_memory_dir,
    get_second_brain_skills_dir,
    get_second_brain_subagents_dir,
    get_second_brain_tools_dir,
    get_second_brain_learning_dir,
    get_second_brain_projects_dir,
    get_second_brain_agents_dir,
)
from clawg_cli.paths import sanitize_agent_id


def _set_second_brain_root(path: Path) -> None:
    cfg = load_config()
    sb = cfg.get("second_brain")
    if not isinstance(sb, dict):
        sb = {}
    sb["enabled"] = True
    sb["root"] = str(path)
    cfg["second_brain"] = sb
    save_config(cfg)
    os.environ[CLAWG_SECOND_BRAIN_ENV] = str(path)
    os.environ[LEGACY_SECOND_BRAIN_ENV] = str(path)


def _print_status() -> int:
    cfg = load_config()
    root = get_second_brain_root(config=cfg, must_exist=False)
    enabled = bool((cfg.get("second_brain") or {}).get("enabled", True))

    print("\nCLAWG Second Brain")
    print("------------------")
    print(f"Enabled: {enabled}")
    print(f"Root:    {root if root else '(not set)'}")

    if root and root.exists():
        print(f"Exists:  yes")
    elif root:
        print(f"Exists:  no")

    print()
    print("Directories:")
    print(f"  memory:    {get_second_brain_memory_dir(cfg) or '(fallback)'}")
    print(f"  skills:    {get_second_brain_skills_dir(cfg) or '(fallback)'}")
    print(f"  subagents: {get_second_brain_subagents_dir(cfg) or '(not configured)'}")
    print(f"  tools:     {get_second_brain_tools_dir(cfg) or '(not configured)'}")
    print(f"  learning:  {get_second_brain_learning_dir(cfg) or '(not configured)'}")
    print(f"  projects:  {get_second_brain_projects_dir(cfg) or '(not configured)'}")
    print(f"  agents:    {get_second_brain_agents_dir(cfg) or '(not configured)'}")
    print()
    return 0


def _cmd_link(args) -> int:
    if not getattr(args, "path", None):
        print("Error: --path is required for 'second-brain link'.")
        return 1

    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"Error: path does not exist: {target}")
        return 1

    _set_second_brain_root(target)
    print(f"Linked Second Brain root: {target}")

    if getattr(args, "bootstrap", False):
        aid = sanitize_agent_id(getattr(args, "agent_id", None) or "default")
        result = bootstrap_second_brain(target, agent_id=aid, force=bool(getattr(args, "force", False)))
        print(f"Bootstrap complete: {len(result['dirs'])} dirs, {len(result['files'])} files")

    return 0


def _cmd_init(args) -> int:
    cfg = load_config()
    root = None
    if getattr(args, "path", None):
        root = Path(args.path).expanduser().resolve()
    else:
        root = get_second_brain_root(config=cfg, must_exist=False)

    if root is None:
        print("Error: no Second Brain root configured. Use: clawg second-brain link --path <vault>")
        return 1

    root.mkdir(parents=True, exist_ok=True)
    aid = sanitize_agent_id(getattr(args, "agent_id", None) or (cfg.get("second_brain", {}).get("agent_default_id") or "default"))
    result = bootstrap_second_brain(root, agent_id=aid, force=bool(getattr(args, "force", False)))
    _set_second_brain_root(root)

    print(f"Initialized CLAWG Second Brain at: {root}")
    print(f"Created {len(result['dirs'])} directories and {len(result['files'])} files")
    print(f"Active agent profile: {aid}")
    return 0


def second_brain_command(args) -> int:
    action = getattr(args, "sb_action", None) or "status"
    if action == "status":
        return _print_status()
    if action == "link":
        return _cmd_link(args)
    if action == "init":
        return _cmd_init(args)

    print("Usage: clawg second-brain [status|link|init]")
    return 1
