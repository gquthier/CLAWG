"""ACP auth helpers — detect the currently configured clawg provider."""

from __future__ import annotations

from typing import Optional


def detect_provider() -> Optional[str]:
    """Resolve the active clawg runtime provider, or None if unavailable."""
    try:
        from clawg_cli.runtime_provider import resolve_runtime_provider
        runtime = resolve_runtime_provider()
        api_key = runtime.get("api_key")
        provider = runtime.get("provider")
        if isinstance(api_key, str) and api_key.strip() and isinstance(provider, str) and provider.strip():
            return provider.strip().lower()
    except Exception:
        return None
    return None


def has_provider() -> bool:
    """Return True if clawg can resolve any runtime provider credentials."""
    return detect_provider() is not None
