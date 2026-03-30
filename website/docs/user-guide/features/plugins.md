---
sidebar_position: 20
---

# Plugins

clawg has a plugin system for adding custom tools, hooks, and integrations without modifying core code.

**→ [Build a clawg Plugin](/docs/guides/build-a-clawg-plugin)** — step-by-step guide with a complete working example.

## Quick overview

Drop a directory into `~/.clawg/plugins/` with a `plugin.yaml` and Python code:

```
~/.clawg/plugins/my-plugin/
├── plugin.yaml      # manifest
├── __init__.py      # register() — wires schemas to handlers
├── schemas.py       # tool schemas (what the LLM sees)
└── tools.py         # tool handlers (what runs when called)
```

Start clawg — your tools appear alongside built-in tools. The model can call them immediately.

## What plugins can do

| Capability | How |
|-----------|-----|
| Add tools | `ctx.register_tool(name, schema, handler)` |
| Add hooks | `ctx.register_hook("post_tool_call", callback)` |
| Ship data files | `Path(__file__).parent / "data" / "file.yaml"` |
| Bundle skills | Copy `skill.md` to `~/.clawg/skills/` at load time |
| Gate on env vars | `requires_env: [API_KEY]` in plugin.yaml |
| Distribute via pip | `[project.entry-points."clawg_agent.plugins"]` |

## Plugin discovery

| Source | Path | Use case |
|--------|------|----------|
| User | `~/.clawg/plugins/` | Personal plugins |
| Project | `.clawg/plugins/` | Project-specific plugins |
| pip | `clawg_agent.plugins` entry_points | Distributed packages |

## Available hooks

| Hook | Fires when |
|------|-----------|
| `pre_tool_call` | Before any tool executes |
| `post_tool_call` | After any tool returns |
| `pre_llm_call` | Before LLM API request |
| `post_llm_call` | After LLM API response |
| `on_session_start` | Session begins |
| `on_session_end` | Session ends |

## Managing plugins

```
/plugins              # list loaded plugins in a session
clawg config set display.show_cost true  # show cost in status bar
```

See the **[full guide](/docs/guides/build-a-clawg-plugin)** for handler contracts, schema format, hook behavior, error handling, and common mistakes.
