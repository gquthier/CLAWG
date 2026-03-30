---
sidebar_position: 11
title: "ACP Editor Integration"
description: "Use CLAWG inside ACP-compatible editors such as VS Code, Zed, and JetBrains"
---

# ACP Editor Integration

CLAWG can run as an ACP server, letting ACP-compatible editors talk to clawg over stdio and render:

- chat messages
- tool activity
- file diffs
- terminal commands
- approval prompts
- streamed thinking / response chunks

ACP is a good fit when you want clawg to behave like an editor-native coding agent instead of a standalone CLI or messaging bot.

## What clawg exposes in ACP mode

clawg runs with a curated `clawg-acp` toolset designed for editor workflows. It includes:

- file tools: `read_file`, `write_file`, `patch`, `search_files`
- terminal tools: `terminal`, `process`
- web/browser tools
- memory, todo, session search
- skills
- execute_code and delegate_task
- vision

It intentionally excludes things that do not fit typical editor UX, such as messaging delivery and cronjob management.

## Installation

Install clawg normally, then add the ACP extra:

```bash
pip install -e '.[acp]'
```

This installs the `agent-client-protocol` dependency and enables:

- `clawg acp`
- `clawg-acp`
- `python -m acp_adapter`

## Launching the ACP server

Any of the following starts clawg in ACP mode:

```bash
clawg acp
```

```bash
clawg-acp
```

```bash
python -m acp_adapter
```

clawg logs to stderr so stdout remains reserved for ACP JSON-RPC traffic.

## Editor setup

### VS Code

Install an ACP client extension, then point it at the repo's `acp_registry/` directory.

Example settings snippet:

```json
{
  "acpClient.agents": [
    {
      "name": "clawg",
      "registryDir": "/path/to/clawg/acp_registry"
    }
  ]
}
```

### Zed

Example settings snippet:

```json
{
  "acp": {
    "agents": [
      {
        "name": "clawg",
        "registry_dir": "/path/to/clawg/acp_registry"
      }
    ]
  }
}
```

### JetBrains

Use an ACP-compatible plugin and point it at:

```text
/path/to/clawg/acp_registry
```

## Registry manifest

The ACP registry manifest lives at:

```text
acp_registry/agent.json
```

It advertises a command-based agent whose launch command is:

```text
clawg acp
```

## Configuration and credentials

ACP mode uses the same clawg configuration as the CLI:

- `~/.clawg/.env`
- `~/.clawg/config.yaml`
- `~/.clawg/skills/`
- `~/.clawg/state.db`

Provider resolution uses clawg' normal runtime resolver, so ACP inherits the currently configured provider and credentials.

## Session behavior

ACP sessions are tracked by the ACP adapter's in-memory session manager while the server is running.

Each session stores:

- session ID
- working directory
- selected model
- current conversation history
- cancel event

The underlying `AIAgent` still uses clawg' normal persistence/logging paths, but ACP `list/load/resume/fork` are scoped to the currently running ACP server process.

## Working directory behavior

ACP sessions bind the editor's cwd to the clawg task ID so file and terminal tools run relative to the editor workspace, not the server process cwd.

## Approvals

Dangerous terminal commands can be routed back to the editor as approval prompts. ACP approval options are simpler than the CLI flow:

- allow once
- allow always
- deny

On timeout or error, the approval bridge denies the request.

## Troubleshooting

### ACP agent does not appear in the editor

Check:

- the editor is pointed at the correct `acp_registry/` path
- clawg is installed and on your PATH
- the ACP extra is installed (`pip install -e '.[acp]'`)

### ACP starts but immediately errors

Try these checks:

```bash
clawg doctor
clawg status
clawg acp
```

### Missing credentials

ACP mode does not have its own login flow. It uses clawg' existing provider setup. Configure credentials with:

```bash
clawg model
```

or by editing `~/.clawg/.env`.

## See also

- [ACP Internals](../../developer-guide/acp-internals.md)
- [Provider Runtime Resolution](../../developer-guide/provider-runtime.md)
- [Tools Runtime](../../developer-guide/tools-runtime.md)
