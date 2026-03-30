"""
Encrypted API key storage in the CLAWG Second Brain vault.

Keys are stored in ``vault/secrets/keystore.enc`` as an AES-encrypted JSON blob.
The encryption key is derived from a master passphrase stored in ``~/.clawg/.keystore-key``
(auto-generated on first use, never leaves the machine).

Architecture:
    ~/.clawg/.keystore-key          ← 32-byte random master key (chmod 0600)
    vault/secrets/keystore.enc      ← Fernet-encrypted JSON of all secrets
    vault/secrets/catalog.md        ← Plaintext catalog (names + descriptions, NO values)

The catalog.md lets agents know which keys exist without decrypting anything.
The actual values are only decrypted at runtime when needed.

Supports:
    - cryptography.fernet.Fernet  (preferred, if installed)
    - Stdlib fallback using PBKDF2 + XOR stream cipher (no pip install needed)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─── Paths ───

CLAWG_HOME = Path(os.getenv("CLAWG_HOME", Path.home() / ".clawg"))
MASTER_KEY_FILE = CLAWG_HOME / ".keystore-key"
SECRETS_DIR_NAME = "secrets"
KEYSTORE_FILE_NAME = "keystore.enc"
CATALOG_FILE_NAME = "catalog.md"


def _get_vault_root() -> Path | None:
    """Resolve the Second Brain vault root (same logic as paths.py)."""
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
        CLAWG_HOME / "second-brain",
        Path.home() / "Second Brain",
    ]:
        if candidate.is_dir():
            return candidate
    return None


def _secrets_dir() -> Path:
    vault = _get_vault_root()
    if not vault:
        return CLAWG_HOME / SECRETS_DIR_NAME
    return vault / SECRETS_DIR_NAME


def _keystore_path() -> Path:
    return _secrets_dir() / KEYSTORE_FILE_NAME


def _catalog_path() -> Path:
    return _secrets_dir() / CATALOG_FILE_NAME


# ─── File Security ───

def _secure_file(path: Path) -> None:
    try:
        if path.exists():
            os.chmod(path, 0o600)
    except (OSError, NotImplementedError):
        pass


def _secure_dir(path: Path) -> None:
    try:
        os.chmod(path, 0o700)
    except (OSError, NotImplementedError):
        pass


# ─── Master Key Management ───

def _get_or_create_master_key() -> bytes:
    """Return the 32-byte master key, creating it if it doesn't exist."""
    CLAWG_HOME.mkdir(parents=True, exist_ok=True)
    _secure_dir(CLAWG_HOME)

    if MASTER_KEY_FILE.exists():
        raw = MASTER_KEY_FILE.read_bytes().strip()
        key = base64.urlsafe_b64decode(raw)
        if len(key) == 32:
            return key
        logger.warning("Master key file corrupted, regenerating")

    key = secrets.token_bytes(32)
    encoded = base64.urlsafe_b64encode(key)

    fd, tmp = tempfile.mkstemp(dir=str(CLAWG_HOME))
    try:
        os.write(fd, encoded + b"\n")
        os.close(fd)
        os.replace(tmp, str(MASTER_KEY_FILE))
    except Exception:
        os.close(fd)
        os.unlink(tmp)
        raise

    _secure_file(MASTER_KEY_FILE)
    logger.info("Generated new keystore master key")
    return key


# ─── Encryption Layer ───

def _derive_fernet_key(master: bytes) -> bytes:
    """Derive a Fernet-compatible key from the master key."""
    derived = hashlib.pbkdf2_hmac("sha256", master, b"clawg-vault-keystore-v1", 100_000)
    return base64.urlsafe_b64encode(derived)


try:
    from cryptography.fernet import Fernet

    def _encrypt(data: bytes, master_key: bytes) -> bytes:
        f = Fernet(_derive_fernet_key(master_key))
        return f.encrypt(data)

    def _decrypt(token: bytes, master_key: bytes) -> bytes:
        f = Fernet(_derive_fernet_key(master_key))
        return f.decrypt(token)

    ENCRYPTION_BACKEND = "fernet"

except ImportError:
    # Stdlib fallback: PBKDF2 + XOR stream cipher with HMAC authentication
    # Not as strong as Fernet/AES, but provides meaningful protection
    # without requiring pip install cryptography

    def _xor_stream(data: bytes, key_material: bytes) -> bytes:
        """Generate a repeating key stream and XOR."""
        stream = hashlib.pbkdf2_hmac("sha256", key_material, b"stream", 1, dklen=max(len(data), 32))
        # Extend if needed
        while len(stream) < len(data):
            stream += hashlib.pbkdf2_hmac("sha256", key_material, stream[-32:], 1, dklen=32)
        return bytes(a ^ b for a, b in zip(data, stream[:len(data)]))

    def _encrypt(data: bytes, master_key: bytes) -> bytes:
        salt = secrets.token_bytes(16)
        derived = hashlib.pbkdf2_hmac("sha256", master_key, salt, 100_000)
        encrypted = _xor_stream(data, derived)
        mac = hmac.new(derived, salt + encrypted, "sha256").digest()
        payload = salt + mac + encrypted
        return base64.urlsafe_b64encode(payload)

    def _decrypt(token: bytes, master_key: bytes) -> bytes:
        payload = base64.urlsafe_b64decode(token)
        if len(payload) < 48:  # 16 salt + 32 mac + at least 0 data
            raise ValueError("Invalid keystore data")
        salt = payload[:16]
        stored_mac = payload[16:48]
        encrypted = payload[48:]
        derived = hashlib.pbkdf2_hmac("sha256", master_key, salt, 100_000)
        expected_mac = hmac.new(derived, salt + encrypted, "sha256").digest()
        if not hmac.compare_digest(stored_mac, expected_mac):
            raise ValueError("Keystore integrity check failed — wrong key or corrupted data")
        return _xor_stream(encrypted, derived)

    ENCRYPTION_BACKEND = "stdlib-pbkdf2"


# ─── Keystore Operations ───

def _load_keystore() -> dict[str, Any]:
    """Load and decrypt the keystore. Returns empty dict if doesn't exist."""
    ks_path = _keystore_path()
    if not ks_path.exists():
        return {"keys": {}, "version": 1, "created": datetime.now(timezone.utc).isoformat()}

    master = _get_or_create_master_key()
    token = ks_path.read_bytes().strip()
    plaintext = _decrypt(token, master)
    return json.loads(plaintext)


def _save_keystore(data: dict[str, Any]) -> None:
    """Encrypt and save the keystore, then update the catalog."""
    master = _get_or_create_master_key()
    plaintext = json.dumps(data, indent=2, default=str).encode("utf-8")
    encrypted = _encrypt(plaintext, master)

    secrets_dir = _secrets_dir()
    secrets_dir.mkdir(parents=True, exist_ok=True)
    _secure_dir(secrets_dir)

    ks_path = _keystore_path()

    fd, tmp = tempfile.mkstemp(dir=str(secrets_dir))
    try:
        os.write(fd, encrypted + b"\n")
        os.close(fd)
        os.replace(tmp, str(ks_path))
    except Exception:
        os.close(fd)
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

    _secure_file(ks_path)
    _update_catalog(data)


def _update_catalog(data: dict[str, Any]) -> None:
    """Write the plaintext catalog.md (names and descriptions only, NO values)."""
    keys = data.get("keys", {})
    lines = [
        "# Secret Keys Catalog",
        "",
        "This file lists all stored API keys and secrets. **Values are encrypted** in `keystore.enc`.",
        "",
        f"Total keys: {len(keys)} | Encryption: {ENCRYPTION_BACKEND}",
        f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "| Key Name | Service | Description | Added | Used By |",
        "|----------|---------|-------------|-------|---------|",
    ]

    for name, meta in sorted(keys.items()):
        service = meta.get("service", "—")
        desc = meta.get("description", "—")
        added = meta.get("added", "—")
        if isinstance(added, str) and "T" in added:
            added = added.split("T")[0]
        used_by = ", ".join(meta.get("used_by", [])) or "all agents"
        lines.append(f"| `{name}` | {service} | {desc} | {added} | {used_by} |")

    lines.extend([
        "",
        "## How to Use",
        "",
        "Agents automatically retrieve keys when needed. To add a new key:",
        "- Tell any agent: \"Save this API key for [service]: [key]\"",
        "- Or use the tool: `vault_keystore_save(name, value, service, description)`",
        "",
        "Keys are encrypted with " + ENCRYPTION_BACKEND + " and stored in `keystore.enc`.",
        "The master encryption key is in `~/.clawg/.keystore-key` (never leaves your machine).",
        "",
    ])

    catalog_path = _catalog_path()
    catalog_path.write_text("\n".join(lines), encoding="utf-8")


# ─── Public API ───

def save_key(
    name: str,
    value: str,
    service: str = "",
    description: str = "",
    used_by: list[str] | None = None,
) -> dict[str, str]:
    """Save an API key to the encrypted vault keystore.

    Also exports to ~/.clawg/.env for backward compatibility with tools
    that use os.getenv().
    """
    name = name.strip().upper()
    if not name:
        return {"error": "Key name is required"}
    if not value:
        return {"error": "Key value is required"}

    data = _load_keystore()
    keys = data.setdefault("keys", {})

    existing = keys.get(name)
    keys[name] = {
        "service": service or _infer_service(name),
        "description": description or _infer_description(name),
        "added": existing["added"] if existing else datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(),
        "used_by": used_by or (existing or {}).get("used_by", []),
        "value": value,
    }

    _save_keystore(data)

    # Also export to .env for backward compat
    _export_to_dotenv(name, value)

    action = "updated" if existing else "saved"
    return {
        "status": "ok",
        "message": f"Key `{name}` {action} securely (encrypted with {ENCRYPTION_BACKEND})",
        "name": name,
        "service": keys[name]["service"],
    }


def get_key(name: str) -> str | None:
    """Retrieve a decrypted API key by name. Returns None if not found."""
    name = name.strip().upper()

    # Try vault keystore first
    try:
        data = _load_keystore()
        entry = data.get("keys", {}).get(name)
        if entry and entry.get("value"):
            return entry["value"]
    except Exception as e:
        logger.warning("Keystore read failed for %s: %s", name, e)

    # Fallback to environment variable
    return os.getenv(name)


def list_keys() -> list[dict[str, str]]:
    """List all stored keys (names and metadata only, NO values)."""
    try:
        data = _load_keystore()
    except Exception:
        return []

    result = []
    for name, meta in sorted(data.get("keys", {}).items()):
        result.append({
            "name": name,
            "service": meta.get("service", ""),
            "description": meta.get("description", ""),
            "added": meta.get("added", ""),
            "used_by": meta.get("used_by", []),
            "has_value": bool(meta.get("value")),
        })
    return result


def delete_key(name: str) -> dict[str, str]:
    """Remove a key from the vault keystore."""
    name = name.strip().upper()
    data = _load_keystore()
    keys = data.get("keys", {})

    if name not in keys:
        return {"error": f"Key `{name}` not found in keystore"}

    del keys[name]
    _save_keystore(data)

    return {"status": "ok", "message": f"Key `{name}` removed from keystore"}


def get_key_for_tool(env_var_name: str) -> str | None:
    """Auto-retrieve a key for a tool that needs it.

    Called by the tool system when a tool requires an env var that isn't set.
    Checks the vault keystore and injects into os.environ if found.
    """
    value = get_key(env_var_name)
    if value:
        os.environ[env_var_name] = value
    return value


# ─── Helpers ───

_SERVICE_MAP = {
    "OPENAI": "OpenAI",
    "ANTHROPIC": "Anthropic",
    "OPENROUTER": "OpenRouter",
    "GOOGLE": "Google",
    "GEMINI": "Google Gemini",
    "ELEVENLABS": "ElevenLabs",
    "TELEGRAM": "Telegram",
    "DISCORD": "Discord",
    "SLACK": "Slack",
    "GITHUB": "GitHub",
    "FIRECRAWL": "Firecrawl",
    "TAVILY": "Tavily",
    "BROWSERBASE": "Browserbase",
    "HASS": "Home Assistant",
    "TWILIO": "Twilio",
    "STRIPE": "Stripe",
    "RESEND": "Resend",
    "SUPABASE": "Supabase",
    "MATRIX": "Matrix",
    "SIGNAL": "Signal",
    "WANDB": "Weights & Biases",
    "DEEPSEEK": "DeepSeek",
    "MISTRAL": "Mistral",
    "REPLICATE": "Replicate",
    "HUGGINGFACE": "Hugging Face",
    "NOUS": "Nous Research",
    "COHERE": "Cohere",
    "PERPLEXITY": "Perplexity",
}


def _infer_service(name: str) -> str:
    """Guess the service from the env var name."""
    upper = name.upper()
    for prefix, service in _SERVICE_MAP.items():
        if prefix in upper:
            return service
    return ""


def _infer_description(name: str) -> str:
    """Guess description from the env var name."""
    upper = name.upper()
    if "TOKEN" in upper:
        return "Authentication token"
    if "SECRET" in upper:
        return "Secret key"
    if "API_KEY" in upper or "APIKEY" in upper:
        return "API key"
    if "PASSWORD" in upper:
        return "Password"
    return "Secret"


def _export_to_dotenv(name: str, value: str) -> None:
    """Write key to ~/.clawg/.env for backward compatibility."""
    env_path = CLAWG_HOME / ".env"
    CLAWG_HOME.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    found = False

    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{name}=") or stripped.startswith(f"{name} ="):
                lines.append(f"{name}={value}")
                found = True
            else:
                lines.append(line)

    if not found:
        lines.append(f"{name}={value}")

    fd, tmp = tempfile.mkstemp(dir=str(CLAWG_HOME))
    try:
        os.write(fd, ("\n".join(lines) + "\n").encode("utf-8"))
        os.close(fd)
        os.replace(tmp, str(env_path))
    except Exception:
        os.close(fd)
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

    _secure_file(env_path)
    os.environ[name] = value


# ─── API Key Pattern Detection ───

import re

_API_KEY_PATTERNS = [
    # Standard env var formats
    re.compile(r"\b([A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD))\s*[=:]\s*[\"']?(\S+?)[\"']?\s*$", re.MULTILINE),
    # Common key prefixes
    re.compile(r"\b(sk-[a-zA-Z0-9_-]{20,})\b"),           # OpenAI style
    re.compile(r"\b(sk-ant-[a-zA-Z0-9_-]{20,})\b"),       # Anthropic style
    re.compile(r"\b(ghp_[a-zA-Z0-9]{36,})\b"),             # GitHub PAT
    re.compile(r"\b(ghu_[a-zA-Z0-9]{36,})\b"),             # GitHub user token
    re.compile(r"\b(xoxb-[a-zA-Z0-9-]+)\b"),               # Slack bot token
    re.compile(r"\b(xoxp-[a-zA-Z0-9-]+)\b"),               # Slack user token
]


def detect_api_keys_in_message(message: str) -> list[dict[str, str]]:
    """Detect API key patterns in a user message.

    Returns list of {name, value} dicts for keys that should be saved.
    Used by the agent to auto-capture keys the user pastes.
    """
    found: list[dict[str, str]] = []
    seen_values: set[str] = set()

    # Named key=value patterns
    for match in _API_KEY_PATTERNS[0].finditer(message):
        name, value = match.group(1), match.group(2)
        if value not in seen_values and len(value) >= 8:
            found.append({"name": name, "value": value})
            seen_values.add(value)

    # Prefix-based detection
    prefix_names = {
        "sk-ant-": "ANTHROPIC_API_KEY",
        "sk-": "OPENAI_API_KEY",
        "ghp_": "GITHUB_TOKEN",
        "ghu_": "GITHUB_TOKEN",
        "xoxb-": "SLACK_BOT_TOKEN",
        "xoxp-": "SLACK_USER_TOKEN",
    }

    for pattern in _API_KEY_PATTERNS[1:]:
        for match in pattern.finditer(message):
            value = match.group(1)
            if value not in seen_values:
                # Determine name from prefix
                name = "UNKNOWN_API_KEY"
                for prefix, key_name in prefix_names.items():
                    if value.startswith(prefix):
                        name = key_name
                        break
                found.append({"name": name, "value": value})
                seen_values.add(value)

    return found


# ─── Tool Registration ───

from tools.registry import registry

_TOOL_SCHEMAS = {
    "vault_keystore_save": {
        "name": "vault_keystore_save",
        "description": (
            "Save an API key or secret securely in the encrypted vault keystore. "
            "The key is encrypted and stored in the Second Brain vault. "
            "Also exports to ~/.clawg/.env for tool compatibility. "
            "Call this whenever a user provides an API key, token, or secret."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Environment variable name (e.g. OPENAI_API_KEY, TELEGRAM_BOT_TOKEN)"
                },
                "value": {
                    "type": "string",
                    "description": "The secret value to store"
                },
                "service": {
                    "type": "string",
                    "description": "Service name (e.g. OpenAI, Anthropic, GitHub). Auto-detected if empty."
                },
                "description": {
                    "type": "string",
                    "description": "What this key is used for. Auto-detected if empty."
                },
            },
            "required": ["name", "value"],
        },
    },
    "vault_keystore_get": {
        "name": "vault_keystore_get",
        "description": (
            "Retrieve an API key from the encrypted vault keystore. "
            "Returns the decrypted value. Falls back to environment variable if not in keystore. "
            "Call this when you need an API key for a service."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Environment variable name to retrieve (e.g. OPENAI_API_KEY)"
                },
            },
            "required": ["name"],
        },
    },
    "vault_keystore_list": {
        "name": "vault_keystore_list",
        "description": (
            "List all API keys stored in the vault keystore. "
            "Returns names, services, and descriptions — never returns actual secret values. "
            "Use this to check what keys are available before requesting one."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    "vault_keystore_delete": {
        "name": "vault_keystore_delete",
        "description": "Remove an API key from the vault keystore.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Environment variable name to delete"
                },
            },
            "required": ["name"],
        },
    },
}


def _handle_save(args: dict, **kwargs: Any) -> str:
    result = save_key(
        name=args.get("name", ""),
        value=args.get("value", ""),
        service=args.get("service", ""),
        description=args.get("description", ""),
    )
    # Never echo the value back
    return json.dumps({k: v for k, v in result.items() if k != "value"})


def _handle_get(args: dict, **kwargs: Any) -> str:
    name = args.get("name", "").strip().upper()
    value = get_key(name)
    if value:
        # Inject into env for the current process
        os.environ[name] = value
        return json.dumps({
            "status": "ok",
            "name": name,
            "message": f"Key `{name}` retrieved and loaded into environment",
            "available": True,
        })
    return json.dumps({
        "status": "not_found",
        "name": name,
        "message": f"Key `{name}` not found in keystore or environment",
        "available": False,
    })


def _handle_list(args: dict, **kwargs: Any) -> str:
    return json.dumps(list_keys(), default=str)


def _handle_delete(args: dict, **kwargs: Any) -> str:
    return json.dumps(delete_key(args.get("name", "")))


# Register all tools
for tool_name, schema in _TOOL_SCHEMAS.items():
    handler = {
        "vault_keystore_save": _handle_save,
        "vault_keystore_get": _handle_get,
        "vault_keystore_list": _handle_list,
        "vault_keystore_delete": _handle_delete,
    }[tool_name]

    registry.register(
        name=tool_name,
        toolset="vault_keystore",
        schema=schema,
        handler=handler,
        description=schema["description"],
        emoji="🔐",
    )
