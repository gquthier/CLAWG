# CLAWG Second Brain Setup Guide

This guide explains how to run CLAWG with a native shared Obsidian Second Brain so every agent starts with the same context and capability set.

## 1. What this architecture solves

CLAWG is designed around a single markdown source of truth.

- All agents share one Second Brain vault.
- Every session loads the same master context files.
- Each agent still keeps its own identity profile.
- Skills, subagents, tools, and learnings are discoverable from the same place.

Result: no context fragmentation between sessions, terminals, or devices.

## 2. Prerequisites

- macOS, Linux, or WSL2
- `git`
- Obsidian installed (optional for CLI runtime, recommended for editing)
- Obsidian Sync enabled if you want context across multiple machines

## 3. Install CLAWG

```bash
curl -fsSL https://raw.githubusercontent.com/gquthier/CLAWG/main/scripts/install.sh | bash
```

Open a new shell, then validate:

```bash
clawg --version
```

## 4. Link your existing Second Brain

Example path (your current production vault):

```bash
clawg second-brain link --path "/Users/gauthier/Documents/Second Brain OpenClaw - PROD"
```

Validate resolved directories:

```bash
clawg second-brain status
```

You should see resolved folders for root, memory, projects, skills, subagents, tools, learning, and agents.

## 5. Initialize CLAWG templates in the vault

Initialize once per new vault, and once per new agent profile.

```bash
clawg second-brain init --agent-id founder
```

Force overwrite templates when you explicitly want to regenerate:

```bash
clawg second-brain init --agent-id founder --force
```

## 6. Recommended vault layout

Use this as the baseline contract for all agents.

```text
Second Brain/
  Large Memory/
    Projects/
  user.md
  environment.md
  philosophy.md
  api/
  learning/
  tools/
  skills/
  subagents/
  agents/
    founder/
      identity.md
      adjoint.md
      soul.md
```

### Master files

- `user.md`: user profile, preferences, constraints, communication style
- `environment.md`: machine/runtime topology, repos, deployment context, paths
- `philosophy.md`: principles, non-negotiables, decision framework

### Shared capability folders

- `tools/`: global tool docs, contracts, and usage policies
- `skills/`: reusable execution playbooks
- `subagents/`: specialist agent definitions and handoff contracts
- `learning/`: durable lessons and postmortems
- `api/`: integration references, auth expectations, schemas

### Agent-specific profile files

Each agent id has:

- `identity.md`: role, boundaries, communication style
- `adjoint.md`: understanding of other agents and delegation map
- `soul.md`: personality, behavior defaults, long-term alignment

## 7. Starting a session with a specific agent profile

```bash
clawg --agent-id founder
```

You can use different IDs for different operators/domains while keeping the same shared vault.

Examples:

```bash
clawg --agent-id builder
clawg --agent-id researcher
clawg --agent-id ops
```

## 8. Session bootstrap behavior (expected)

On each new CLAWG session:

1. Resolve linked Second Brain root.
2. Load master files (`user.md`, `environment.md`, `philosophy.md`).
3. Load agent profile (`identity.md`, `adjoint.md`, `soul.md`).
4. Expose shared skills/subagents/tools from vault folders.
5. Use this context first before freeform generation.

On each user task:

1. Classify task type.
2. Search relevant learnings, skills, and subagents.
3. Execute with shared tools.
4. Write useful outcomes back to `learning/` or project notes.

## 9. Obsidian workflow

Recommended live workflow:

1. Open the linked vault in Obsidian.
2. Edit context markdown directly (`user.md`, `environment.md`, etc.).
3. Organize reusable procedures in `skills/`.
4. Keep specialist patterns in `subagents/`.
5. Sync across devices with Obsidian Sync.

Because CLAWG reads markdown from the vault path, markdown edits become available to future sessions without extra export steps.

## 10. Skills and subagents conventions

### Skill file convention

Inside `skills/<skill-name>/`:

- `SKILL.md` (required): goal, triggers, constraints, steps
- optional references (`templates/`, `checklists/`, `examples/`)

### Subagent file convention

Inside `subagents/<subagent-name>/`:

- `README.md`: mission and boundaries
- `handoff.md`: expected input/output format
- optional policy/config docs

## 11. Shared tools and API governance

Use one common contract for all agents:

- Put global tool rules in `tools/`.
- Put API schemas and auth notes in `api/`.
- Keep naming stable and explicit.
- Document failure mode and fallback per integration.

If one agent updates a tool contract, all agents immediately benefit from the same updated docs.

## 12. Essential command reference

```bash
# Core
clawg
clawg --agent-id <id>
clawg setup
clawg model
clawg tools
clawg config
clawg doctor
clawg update

# Second Brain
clawg second-brain status
clawg second-brain link --path "<vault-path>"
clawg second-brain init --agent-id <id>
clawg second-brain init --agent-id <id> --force

# Messaging and automation
clawg gateway
clawg gateway setup
clawg cron
```

## 13. Troubleshooting

### `second-brain status` shows wrong paths

- Re-link with an absolute path:
  ```bash
  clawg second-brain link --path "/absolute/path/to/your/vault"
  ```
- Run status again:
  ```bash
  clawg second-brain status
  ```

### Agent cannot find profile files

- Confirm folder exists:
  - `agents/<id>/identity.md`
  - `agents/<id>/adjoint.md`
  - `agents/<id>/soul.md`
- Re-run init for the missing id:
  ```bash
  clawg second-brain init --agent-id <id>
  ```

### Markdown changed in Obsidian but behavior did not update

- Start a new session with the same `--agent-id`.
- Check that edits were made in the linked vault path (not another vault copy).

### Command not found: `clawg`

- Open a new shell after install.
- Verify binary in PATH:
  ```bash
  which clawg
  ```

## 14. Operational best practices

- Keep master files short, explicit, and stable.
- Move ephemeral notes to project files under `Large Memory/Projects/`.
- Add one learning note per meaningful failure.
- Keep skills procedural; avoid vague policy-only text.
- Version the full vault in git when possible.

## 15. Open-source publishing checklist

Before publishing your CLAWG fork:

1. Remove private keys/tokens from `.env` and markdown files.
2. Add a clean sample vault structure in docs.
3. Ensure all links point to your repository namespace.
4. Include an explicit contribution guide for skill/subagent templates.
5. Provide one end-to-end demo scenario in README.

---

If you want, the next step is to add machine-readable templates for `identity.md`, `adjoint.md`, `soul.md`, and a validator command that checks vault compliance before session start.
