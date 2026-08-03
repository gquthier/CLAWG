<div align="center">

<img src="https://img.shields.io/badge/AGENTIC-INFRASTRUCTURE-12A594?style=flat-square&labelColor=12A594&color=1A1A1A" alt="AGENTIC · INFRASTRUCTURE">

<img src="assets/logo.svg" alt="SMART CLAWG" width="560">

# Autonomous Agent Framework

### Every agent you run, working from the same brain.

Stop re-explaining your context to each new session.<br>One shared vault holds who you are, how you work and what you know —<br>and every agent loads it from anywhere.

<br>

<a href="https://bizos.cc">
<img src="https://img.shields.io/badge/BizOS-build%20autonomous%20companies-0A0A0A?style=for-the-badge&labelColor=0A0A0A" alt="BizOS — build autonomous companies">
</a>

<br><br>

<a href="https://x.com/gauthierthiry"><img src="https://img.shields.io/badge/@gauthierthiry-0A0A0A?style=flat-square&logo=x&logoColor=white" alt="X"></a>
<a href="https://youtube.com/@gquthier"><img src="https://img.shields.io/badge/@gquthier-FF0000?style=flat-square&logo=youtube&logoColor=white" alt="YouTube"></a>

<br>

<sub>Open-source framework · native shared Obsidian Second Brain · master context files · shared skills, subagents, tools and APIs · per-agent identity profiles · Obsidian Sync across sessions</sub>

</div>

---

Every session can load shared markdown context from one vault so all agents work from the same source of truth:

- master files (`user.md`, `environment.md`, `philosophy.md`)
- shared capabilities (`skills/`, `subagents/`, `tools/`, `api/`, `learning/`)
- per-agent profile files (`identity.md`, `AGENTS.md`, `soul.md`)

Access your context from any Claude Code session via Obsidian Sync.

## Why CLAWG

- One context runtime for all agents
- Native markdown workflow (edit in Obsidian, reuse in CLI)
- Shared tools and APIs across all agents
- Multi-agent architecture with deterministic profile loading
- Open-source and self-hostable

## Quickstart

### 1) Install

```bash
curl -fsSL https://raw.githubusercontent.com/gquthier/CLAWG/main/scripts/install.sh | bash
```

Supported: macOS, Linux, WSL2.

### 2) Link your vault

```bash
clawg second-brain link --path "/path/to/your/Second Brain"
```

### 3) Initialize templates

```bash
clawg second-brain init --agent-id founder
```

### 4) Validate path resolution

```bash
clawg second-brain status
```

### 5) Start agent session

```bash
clawg --agent-id founder
```

## Core commands

```bash
clawg
clawg setup
clawg model
clawg tools
clawg config
clawg gateway
clawg doctor
clawg update

clawg second-brain status
clawg second-brain link --path "<vault-path>"
clawg second-brain init --agent-id <id>
```

## Second Brain reference layout

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
      AGENTS.md
      soul.md
```

## Documentation

- Landing page source: [`landingpage/index.html`](landingpage/index.html)
- Complete setup guide: [`docs/SECOND_BRAIN_SETUP.md`](docs/SECOND_BRAIN_SETUP.md)
- Additional docs: [`docs/`](docs/)

## Development

```bash
git clone https://github.com/gquthier/CLAWG.git
cd CLAWG
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run checks:

```bash
python -m pytest tests/ -q
```

## Contributing

1. Open an issue describing the change.
2. Create a branch from `main`.
3. Keep pull requests focused and testable.
4. Add docs updates when changing runtime behavior.

## License

MIT - see [`LICENSE`](LICENSE).

---

<div align="center">

<br>

### Building something that runs itself?

**[bizos.cc](https://bizos.cc)** — build autonomous companies.

<br>

<a href="https://x.com/gauthierthiry"><img src="https://img.shields.io/badge/@gauthierthiry-0A0A0A?style=flat-square&logo=x&logoColor=white" alt="X"></a>
<a href="https://youtube.com/@gquthier"><img src="https://img.shields.io/badge/@gquthier-FF0000?style=flat-square&logo=youtube&logoColor=white" alt="YouTube"></a>

<br><br>

<sub>Built by <a href="https://x.com/gauthierthiry">Gauthier Thiry</a></sub>

</div>
