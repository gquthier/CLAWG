---
sidebar_position: 1
title: "Quickstart"
description: "Your first conversation with CLAWG — from install to chatting in 2 minutes"
---

# Quickstart

This guide walks you through installing CLAWG, setting up a provider, and having your first conversation. By the end, you'll know the key features and how to explore further.

## 1. Install CLAWG

Run the one-line installer:

```bash
# Linux / macOS / WSL2
curl -fsSL https://raw.githubusercontent.com/NousResearch/clawg/main/scripts/install.sh | bash
```

:::tip Windows Users
Install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) first, then run the command above inside your WSL2 terminal.
:::

After it finishes, reload your shell:

```bash
source ~/.bashrc   # or source ~/.zshrc
```

## 2. Set Up a Provider

The installer configures your LLM provider automatically. To change it later, use one of these commands:

```bash
clawg model       # Choose your LLM provider and model
clawg tools       # Configure which tools are enabled
clawg setup       # Or configure everything at once
```

`clawg model` walks you through selecting an inference provider:

| Provider | What it is | How to set up |
|----------|-----------|---------------|
| **Nous Portal** | Subscription-based, zero-config | OAuth login via `clawg model` |
| **OpenAI Codex** | ChatGPT OAuth, uses Codex models | Device code auth via `clawg model` |
| **Anthropic** | Claude models directly (Pro/Max or API key) | `clawg model` with Claude Code auth, or an Anthropic API key |
| **OpenRouter** | Multi-provider routing across many models | Enter your API key |
| **Z.AI** | GLM / Zhipu-hosted models | Set `GLM_API_KEY` / `ZAI_API_KEY` |
| **Kimi / Moonshot** | Moonshot-hosted coding and chat models | Set `KIMI_API_KEY` |
| **MiniMax** | International MiniMax endpoint | Set `MINIMAX_API_KEY` |
| **MiniMax China** | China-region MiniMax endpoint | Set `MINIMAX_CN_API_KEY` |
| **Alibaba Cloud** | Qwen models via DashScope | Set `DASHSCOPE_API_KEY` |
| **Kilo Code** | KiloCode-hosted models | Set `KILOCODE_API_KEY` |
| **OpenCode Zen** | Pay-as-you-go access to curated models | Set `OPENCODE_ZEN_API_KEY` |
| **OpenCode Go** | $10/month subscription for open models | Set `OPENCODE_GO_API_KEY` |
| **Vercel AI Gateway** | Vercel AI Gateway routing | Set `AI_GATEWAY_API_KEY` |
| **Custom Endpoint** | VLLM, SGLang, Ollama, or any OpenAI-compatible API | Set base URL + API key |

:::tip
You can switch providers at any time with `clawg model` — no code changes, no lock-in. When configuring a custom endpoint, clawg will prompt for the context window size and auto-detect it when possible. See [Context Length Detection](../user-guide/configuration.md#context-length-detection) for details.
:::

## 3. Start Chatting

```bash
clawg
```

That's it! You'll see a welcome banner with your model, available tools, and skills. Type a message and press Enter.

```
❯ What can you help me with?
```

The agent has access to tools for web search, file operations, terminal commands, and more — all out of the box.

## 4. Try Key Features

### Ask it to use the terminal

```
❯ What's my disk usage? Show the top 5 largest directories.
```

The agent will run terminal commands on your behalf and show you the results.

### Use slash commands

Type `/` to see an autocomplete dropdown of all commands:

| Command | What it does |
|---------|-------------|
| `/help` | Show all available commands |
| `/tools` | List available tools |
| `/model` | Switch models interactively |
| `/personality pirate` | Try a fun personality |
| `/save` | Save the conversation |

### Multi-line input

Press `Alt+Enter` or `Ctrl+J` to add a new line. Great for pasting code or writing detailed prompts.

### Interrupt the agent

If the agent is taking too long, just type a new message and press Enter — it interrupts the current task and switches to your new instructions. `Ctrl+C` also works.

### Resume a session

When you exit, clawg prints a resume command:

```bash
clawg --continue    # Resume the most recent session
clawg -c            # Short form
```

## 5. Explore Further

Here are some things to try next:

### Set up a sandboxed terminal

For safety, run the agent in a Docker container or on a remote server:

```bash
clawg config set terminal.backend docker    # Docker isolation
clawg config set terminal.backend ssh       # Remote server
```

### Connect messaging platforms

Chat with clawg from your phone or other surfaces via Telegram, Discord, Slack, WhatsApp, Signal, Email, or Home Assistant:

```bash
clawg gateway setup    # Interactive platform configuration
```

### Add voice mode

Want microphone input in the CLI or spoken replies in messaging?

```bash
pip install clawg[voice]

# Optional but recommended for free local speech-to-text
pip install faster-whisper
```

Then start clawg and enable it inside the CLI:

```text
/voice on
```

Press `Ctrl+B` to record, or use `/voice tts` to have clawg speak its replies. See [Voice Mode](../user-guide/features/voice-mode.md) for the full setup across CLI, Telegram, Discord, and Discord voice channels.

### Schedule automated tasks

```
❯ Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.
```

The agent will set up a cron job that runs automatically via the gateway.

### Browse and install skills

```bash
clawg skills search kubernetes
clawg skills search react --source skills-sh
clawg skills search https://mintlify.com/docs --source well-known
clawg skills install openai/skills/k8s
clawg skills install official/security/1password
clawg skills install skills-sh/vercel-labs/json-render/json-render-react --force
```

Tips:
- Use `--source skills-sh` to search the public `skills.sh` directory.
- Use `--source well-known` with a docs/site URL to discover skills from `/.well-known/skills/index.json`.
- Use `--force` only after reviewing a third-party skill. It can override non-dangerous policy blocks, but not a `dangerous` scan verdict.

Or use the `/skills` slash command inside chat.

### Use clawg inside an editor via ACP

clawg can also run as an ACP server for ACP-compatible editors like VS Code, Zed, and JetBrains:

```bash
pip install -e '.[acp]'
clawg acp
```

See [ACP Editor Integration](../user-guide/features/acp.md) for setup details.

### Try MCP servers

Connect to external tools via the Model Context Protocol:

```yaml
# Add to ~/.clawg/config.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `clawg` | Start chatting |
| `clawg model` | Choose your LLM provider and model |
| `clawg tools` | Configure which tools are enabled per platform |
| `clawg setup` | Full setup wizard (configures everything at once) |
| `clawg doctor` | Diagnose issues |
| `clawg update` | Update to latest version |
| `clawg gateway` | Start the messaging gateway |
| `clawg --continue` | Resume last session |

## Next Steps

- **[CLI Guide](../user-guide/cli.md)** — Master the terminal interface
- **[Configuration](../user-guide/configuration.md)** — Customize your setup
- **[Messaging Gateway](../user-guide/messaging/index.md)** — Connect Telegram, Discord, Slack, WhatsApp, Signal, Email, or Home Assistant
- **[Tools & Toolsets](../user-guide/features/tools.md)** — Explore available capabilities
