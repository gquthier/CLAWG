# Skills Registry

> **For agents**: Read this file BEFORE executing any task. If a skill matches the task, load it with `skill_view <category>/<name>` instead of reinventing the procedure.

32 pre-installed skills across 7 categories.

---

## Quick Navigation

| Category | Count | When to use |
|----------|-------|-------------|
| [Development](#development) | 7 | Planning, TDD, debugging, code review, delegation |
| [GitHub](#github) | 6 | Repos, issues, PRs, CI, code review |
| [Productivity](#productivity) | 6 | Google Workspace, Notion, Linear, PDF, OCR, PPTX |
| [Research](#research) | 3 | Web search, academic papers, feed monitoring |
| [Communication](#communication) | 5 | Email, iMessage, Apple Notes/Reminders, FindMy |
| [Content](#content) | 3 | YouTube transcripts, diagrams, ASCII art |
| [Integration](#integration) | 3 | MCP servers, vault dashboards |

---

## Development

| Skill | Path | What it does |
|-------|------|-------------|
| Plan | `software-development/plan` | Create structured implementation plans |
| Writing Plans | `software-development/writing-plans` | Multi-step task planning with specs |
| TDD | `software-development/test-driven-development` | Test first, implement, refactor |
| Debugging | `software-development/systematic-debugging` | Root cause analysis for bugs and failures |
| Code Review | `software-development/code-review` | Thorough review with security focus |
| Request Review | `software-development/requesting-code-review` | Post-implementation review checklist |
| Subagent Dev | `software-development/subagent-driven-development` | Parallel task execution with subagents |

## GitHub

| Skill | Path | What it does |
|-------|------|-------------|
| Auth | `github/github-auth` | Set up git/gh authentication |
| Repos | `github/github-repo-management` | Clone, create, fork, configure |
| Issues | `github/github-issues` | Create, triage, close issues |
| PR Workflow | `github/github-pr-workflow` | Branch, commit, PR, CI, merge |
| Code Review | `github/github-code-review` | Inline PR review with diff analysis |
| Inspection | `github/codebase-inspection` | LOC counting, language breakdown |

## Productivity

| Skill | Path | What it does |
|-------|------|-------------|
| Google Workspace | `productivity/google-workspace` | Gmail, Calendar, Drive, Sheets, Docs |
| Notion | `productivity/notion` | Pages, databases, blocks via API |
| Linear | `productivity/linear` | Issues, projects, teams via GraphQL |
| PDF | `productivity/nano-pdf` | Edit PDFs with natural language |
| OCR | `productivity/ocr-and-documents` | Extract text from PDFs and scans |
| PowerPoint | `productivity/powerpoint` | Create and edit .pptx presentations |

## Research

| Skill | Path | What it does |
|-------|------|-------------|
| Web Search | `research/duckduckgo-search` | Free web search (text, news, images) |
| arXiv | `research/arxiv` | Search academic papers |
| Blog Watch | `research/blogwatcher` | Monitor RSS/Atom feeds for updates |

## Communication

| Skill | Path | What it does |
|-------|------|-------------|
| Email | `email/himalaya` | Read, write, search emails via IMAP/SMTP |
| iMessage | `apple/imessage` | Send/receive iMessages via CLI |
| Apple Notes | `apple/apple-notes` | Manage Apple Notes |
| Reminders | `apple/apple-reminders` | Manage Apple Reminders |
| FindMy | `apple/findmy` | Track Apple devices and AirTags |

## Content

| Skill | Path | What it does |
|-------|------|-------------|
| YouTube | `media/youtube-content` | Fetch transcripts, generate summaries |
| Excalidraw | `creative/excalidraw` | Hand-drawn style diagrams |
| ASCII Art | `creative/ascii-art` | Generate ASCII art (571 fonts) |

## Integration

| Skill | Path | What it does |
|-------|------|-------------|
| Native MCP | `mcp/native-mcp` | Connect to any MCP server |
| mcporter | `mcp/mcporter` | List, configure, call MCP tools |
| Dashboard | `note-taking/obsidian-dashboard` | Vault dashboards and visualization |

---

## How to Use a Skill

```
1. Find the skill in the table above
2. Run: skill_view <path>        (e.g. skill_view software-development/plan)
3. Follow the instructions in the SKILL.md
```

## How to Add a New Skill

When you create a new skill, follow these steps so other agents can find it:

### 1. Create the skill folder and SKILL.md

```
skills/<category>/<skill-name>/SKILL.md
```

### 2. SKILL.md format

```yaml
---
name: "skill-name"
description: "One-line description of what this skill does"
category: "category"
platforms: [darwin, linux, win32]   # optional — omit to support all
---

# Skill Name

Step-by-step instructions for the agent...
```

### 3. Update this index

Add one row to the correct category table:

```markdown
| Short Name | `category/skill-name` | One-line description |
```

If the skill doesn't fit an existing category, create a new `##` section and add it to the Quick Navigation table at the top with a count and a "When to use" hint.

### Rules

- One SKILL.md per folder. No nested skills.
- Description must be under 60 characters. Agents scan fast.
- If the skill overlaps with a native tool (see `environment.md` > Vault Paths), do NOT add it — use the native tool instead.
- Skills are shared across ALL agents in the vault. Write them for any agent, not just yours.
