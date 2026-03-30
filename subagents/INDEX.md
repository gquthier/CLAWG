# CLAWG Subagents Registry

Pre-installed agents organized by division. Each agent is a markdown prompt file that can be loaded by any CLAWG session.

## Divisions

| Division | Agents | Focus |
|----------|--------|-------|
| engineering | 26 | Frontend, backend, DevOps, security, data, AI |
| design | 8 | UI/UX, branding, visual storytelling |
| marketing | 29 | Growth, social media, SEO, content |
| paid-media | 7 | PPC, programmatic, tracking |
| sales | 8 | Outbound, deals, pipeline, coaching |
| product | 5 | Sprint planning, feedback, research |
| project-management | 6 | Orchestration, operations, experiments |
| testing | 8 | QA, performance, accessibility |
| support | 6 | Customer service, analytics, finance, legal |
| spatial-computing | 6 | XR, visionOS, Metal, WebXR |
| specialized | 14 | Multi-agent orchestration, compliance, ZK |
| academic | varies | Research, writing, peer review |
| game-development | varies | Game design, mechanics, engines |
| strategy | varies | Business strategy, competitive analysis |

## Usage

Agents are automatically discoverable by CLAWG when linked to a Second Brain vault.
Load a specific agent profile:

```bash
clawg --agent-id <division>/<agent-name>
```

Or reference in your vault's `AGENTS.md` for delegation rules.
