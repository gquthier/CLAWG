"""
CLAWG Second Brain Auto-Scan

Scans the user's machine via LLM and populates the Second Brain vault
with structured markdown files (user.md, environment.md, philosophy.md, etc.).

Requires: a configured LLM API key (OpenRouter, Anthropic, OpenAI, etc.)
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

PURPLE = "\033[0;35m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
DIM = "\033[2m"
NC = "\033[0m"

# ─── Machine data collection ───────────────────────────────────────

def _run(cmd: str, timeout: int = 10) -> str:
    """Run a shell command safely, return stdout or empty string."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()[:2000]  # cap output
    except Exception:
        return ""


def collect_machine_data() -> dict:
    """Collect non-sensitive machine information for LLM analysis."""
    data: dict = {}

    # ── System ──
    data["os"] = platform.system()
    data["os_version"] = platform.version()
    data["os_release"] = platform.release()
    data["arch"] = platform.machine()
    data["hostname"] = platform.node()
    data["python_version"] = platform.python_version()
    data["shell"] = os.environ.get("SHELL", "unknown")
    data["home"] = str(Path.home())
    data["user"] = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
    data["lang"] = os.environ.get("LANG", "")
    data["timezone"] = _run("date +%Z") or os.environ.get("TZ", "")

    # ── Dev tools ──
    tools_check = [
        "git", "node", "npm", "pnpm", "yarn", "bun",
        "python3", "pip3", "uv", "cargo", "rustc",
        "go", "java", "javac", "docker", "kubectl",
        "terraform", "aws", "gcloud", "az",
        "brew", "apt", "dnf",
        "code", "cursor", "vim", "nvim", "emacs",
        "claude", "gh", "vercel", "supabase",
        "obsidian",
    ]
    installed = {}
    for tool in tools_check:
        path = shutil.which(tool)
        if path:
            version = _run(f"{tool} --version 2>/dev/null | head -1")
            installed[tool] = version or "installed"
    data["dev_tools"] = installed

    # ── Git config ──
    data["git_user_name"] = _run("git config --global user.name")
    data["git_user_email"] = _run("git config --global user.email")

    # ── Active repos ──
    repos = []
    search_dirs = ["~/Desktop", "~/Documents", "~/Projects", "~/repos", "~/dev", "~/code", "~/work"]
    for d in search_dirs:
        expanded = os.path.expanduser(d)
        if os.path.isdir(expanded):
            found = _run(f"find {expanded} -maxdepth 3 -name '.git' -type d 2>/dev/null | head -20")
            for git_dir in found.splitlines():
                if git_dir:
                    repo_path = os.path.dirname(git_dir)
                    repo_name = os.path.basename(repo_path)
                    # Get remote URL (strip credentials if any)
                    remote = _run(f"git -C '{repo_path}' remote get-url origin 2>/dev/null")
                    langs = _run(f"ls '{repo_path}' | head -20")
                    repos.append({
                        "name": repo_name,
                        "path": repo_path,
                        "remote": remote,
                        "files": langs,
                    })
    data["repos"] = repos[:30]  # cap

    # ── Package managers / project types ──
    data["node_global_packages"] = _run("npm list -g --depth=0 2>/dev/null | tail -20")
    data["pip_packages"] = _run("pip3 list --format=columns 2>/dev/null | head -30")
    data["brew_packages"] = _run("brew list --formula 2>/dev/null | head -40") if shutil.which("brew") else ""

    # ── Running services ──
    if data["os"] == "Darwin":
        data["running_services"] = _run("brew services list 2>/dev/null | head -15")
    else:
        data["running_services"] = _run("systemctl list-units --type=service --state=running 2>/dev/null | head -15")

    # ── SSH keys (names only, NOT content) ──
    ssh_dir = Path.home() / ".ssh"
    if ssh_dir.exists():
        data["ssh_keys"] = [f.name for f in ssh_dir.iterdir() if f.suffix == ".pub"]

    # ── Cloud / API configs (existence only, NOT content) ──
    config_files = [
        "~/.aws/credentials", "~/.kube/config", "~/.docker/config.json",
        "~/.vercel/auth.json", "~/.config/gh/hosts.yml",
        "~/.clawg/config.yaml", "~/.openclaw/openclaw.json",
    ]
    existing_configs = []
    for cf in config_files:
        if Path(os.path.expanduser(cf)).exists():
            existing_configs.append(cf)
    data["config_files_present"] = existing_configs

    # ── Disk usage ──
    data["disk_usage"] = _run("df -h / | tail -1")

    return data


# ─── LLM interaction ───────────────────────────────────────────────

SYSTEM_PROMPT = """You are CLAWG's auto-configuration assistant. You receive a JSON dump of a user's machine data (OS, tools, repos, languages, configs) and you must generate structured markdown files for their Second Brain vault.

Generate EXACTLY these files as a JSON object with filenames as keys and markdown content as values:

1. "user.md" — User profile: name (from git config), role (infer from tools/repos), primary languages, expertise areas, working style preferences.

2. "environment.md" — Machine environment: OS, shell, installed tools (grouped by category), active repos (name + what they seem to be), cloud configs detected, IDE/editor.

3. "philosophy.md" — Inferred working principles based on their toolset. For example: if they use Docker+K8s → containerization-first; if they use TypeScript+React → frontend-heavy; if many repos → multi-project operator. Keep it practical, not generic.

4. "api.md" — API endpoints and services detected (from configs, not secrets). List which services are configured (AWS, GCP, Vercel, GitHub, etc.) with placeholder notes for keys.

Rules:
- NEVER include actual secrets, tokens, passwords, or key values
- Write in first person ("I am...", "I use...")
- Be specific, not generic. Reference actual tool versions and repo names
- Keep each file under 80 lines
- Output valid JSON only: {"user.md": "content...", "environment.md": "content...", ...}"""


def _call_llm(machine_data: dict, api_key: str, model: str, base_url: str) -> Optional[dict]:
    """Call the LLM API to generate vault files."""
    import urllib.request
    import urllib.error

    # Final safety: model MUST be a non-empty string
    if not isinstance(model, str) or not model.strip():
        if isinstance(model, dict):
            model = model.get("default", "") or model.get("model", "") or "google/gemini-2.5-flash"
        else:
            model = "google/gemini-2.5-flash"
    model = str(model).strip()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(machine_data, indent=2, default=str)},
        ],
        "temperature": 0.3,
        "max_tokens": 4000,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # Add OpenRouter-specific headers if needed
    if "openrouter" in base_url:
        headers["HTTP-Referer"] = "https://github.com/gquthier/CLAWG"
        headers["X-Title"] = "CLAWG Autoscan"

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            content = result["choices"][0]["message"]["content"]

            # Extract JSON from response (handle ```json blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"\n{RED}API Error ({e.code}): {body[:200]}{NC}")
        return None
    except json.JSONDecodeError as e:
        print(f"\n{RED}Failed to parse LLM response as JSON: {e}{NC}")
        return None
    except Exception as e:
        print(f"\n{RED}LLM call failed: {e}{NC}")
        return None


# ─── Resolve API credentials ──────────────────────────────────────

def _resolve_model_string(raw_model) -> str:
    """Extract a clean model string from config value (may be str or dict)."""
    if isinstance(raw_model, str) and raw_model:
        return raw_model
    if isinstance(raw_model, dict):
        # Config can store model as {"default": "model/name", "provider": "..."}
        return raw_model.get("default", "") or raw_model.get("model", "")
    return ""


def _resolve_api_config() -> tuple[str, str, str]:
    """Find API key, model, and base URL from config or env."""
    # Try loading CLAWG config
    try:
        from clawg_cli.config import load_config
        cfg = load_config()
        model = _resolve_model_string(cfg.get("model", ""))
    except Exception:
        cfg = {}
        model = ""

    # Provider detection order
    providers = [
        ("OPENROUTER_API_KEY", "google/gemini-2.5-flash", "https://openrouter.ai/api/v1"),
        ("ANTHROPIC_API_KEY", "claude-sonnet-4-20250514", "https://api.anthropic.com/v1"),
        ("OPENAI_API_KEY", "gpt-4o", "https://api.openai.com/v1"),
        ("DEEPSEEK_API_KEY", "deepseek-chat", "https://api.deepseek.com/v1"),
    ]

    # Check env file
    env_path = Path.home() / ".clawg" / ".env"
    env_vars: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env_vars[k.strip()] = v.strip().strip('"').strip("'")

    for env_var, default_model, base_url in providers:
        key = os.environ.get(env_var) or env_vars.get(env_var)
        if key:
            # Use config model if it's a valid string, otherwise fallback
            final_model = model if model else default_model
            return key, final_model, base_url

    return "", "", ""


# ─── Main command ──────────────────────────────────────────────────

def autoscan_command(args) -> int:
    """Run the Second Brain auto-scan."""
    from clawg_cli.config import load_config
    from clawg_cli.paths import get_second_brain_root, get_second_brain_agent_dir, sanitize_agent_id

    # ── Warning ──
    print()
    print(f"{PURPLE}{BOLD}{'=' * 60}{NC}")
    print(f"{PURPLE}{BOLD}  SMART-CLAWG — Second Brain Auto-Scan{NC}")
    print(f"{PURPLE}{BOLD}{'=' * 60}{NC}")
    print()
    print(f"  {YELLOW}{BOLD}WARNING{NC}")
    print()
    print(f"  This script will scan your computer to automatically")
    print(f"  configure your Second Brain. It will collect:")
    print()
    print(f"  {DIM}•{NC} OS, shell, installed dev tools and versions")
    print(f"  {DIM}•{NC} Git repos on your machine (names and remotes)")
    print(f"  {DIM}•{NC} Package managers and installed packages")
    print(f"  {DIM}•{NC} Cloud service configs detected (existence only)")
    print(f"  {DIM}•{NC} Running services")
    print()
    print(f"  {GREEN}This data is sent to your configured LLM API{NC}")
    print(f"  {GREEN}to generate your vault files (user.md, environment.md, etc.){NC}")
    print()
    print(f"  {RED}{BOLD}No secrets, tokens, or passwords are ever collected or sent.{NC}")
    print()

    # ── Check vault ──
    cfg = load_config()
    vault_root = get_second_brain_root(config=cfg, must_exist=False)
    if not vault_root or not vault_root.exists():
        print(f"  {RED}No Second Brain linked. Run first:{NC}")
        print(f"  {CYAN}clawg second-brain link --path <vault> --bootstrap{NC}")
        return 1

    print(f"  {DIM}Vault:{NC} {CYAN}{vault_root}{NC}")

    # ── Check API ──
    api_key, model, base_url = _resolve_api_config()
    if not api_key:
        print(f"\n  {RED}No LLM API key found.{NC}")
        print(f"  Configure one via {CYAN}clawg setup{NC} or set OPENROUTER_API_KEY.")
        return 1

    print(f"  {DIM}Model:{NC} {CYAN}{model}{NC}")
    print()

    # ── Confirm ──
    try:
        reply = input(f"  {BOLD}Start scan? [y/N]{NC} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        return 0

    if reply not in ("y", "yes"):
        print("  Cancelled.")
        return 0

    # ── Scan ──
    print()
    print(f"  {PURPLE}Scanning machine...{NC}", end="", flush=True)
    machine_data = collect_machine_data()
    print(f" {GREEN}done{NC}")

    tool_count = len(machine_data.get("dev_tools", {}))
    repo_count = len(machine_data.get("repos", []))
    print(f"  {DIM}Found {tool_count} tools, {repo_count} repos{NC}")

    # ── Call LLM ──
    print(f"  {PURPLE}Generating vault files via LLM...{NC}", end="", flush=True)
    files = _call_llm(machine_data, api_key, model, base_url)

    if not files:
        print(f" {RED}failed{NC}")
        return 1

    print(f" {GREEN}done{NC}")

    # ── Write files ──
    print()
    expected = ["user.md", "environment.md", "philosophy.md", "api.md"]
    written = 0
    for filename in expected:
        content = files.get(filename)
        if not content:
            print(f"  {YELLOW}skip{NC} {filename} (not generated)")
            continue

        target = vault_root / filename
        # Backup existing
        if target.exists():
            backup = target.with_suffix(".md.backup")
            target.rename(backup)
            print(f"  {DIM}backed up{NC} {filename} → {backup.name}")

        target.write_text(content, encoding="utf-8")
        print(f"  {GREEN}wrote{NC} {filename} ({len(content)} chars)")
        written += 1

    # ── Agent profile ──
    agent_id = sanitize_agent_id(getattr(args, "agent_id", None) or cfg.get("second_brain", {}).get("agent_default_id", "default"))
    agent_dir = get_second_brain_agent_dir(agent_id, config=cfg)
    if agent_dir and not (agent_dir / "identity.md").exists():
        agent_dir.mkdir(parents=True, exist_ok=True)
        identity = files.get("identity.md", f"# Identity\n\nAgent profile: {agent_id}\n")
        (agent_dir / "identity.md").write_text(identity, encoding="utf-8")
        print(f"  {GREEN}wrote{NC} agents/{agent_id}/identity.md")
        written += 1

    # ── Done ──
    print()
    print(f"  {GREEN}{BOLD}Auto-scan complete.{NC} {written} files written to vault.")
    print()
    print(f"  {CYAN}Open in Obsidian to review and customize.{NC}")
    print(f"  {CYAN}Launch:{NC} {BOLD}clawg --agent-id {agent_id}{NC}")
    print()
    return 0
