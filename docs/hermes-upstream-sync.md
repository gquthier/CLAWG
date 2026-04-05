# Hermes → CLAWG Sync Flow

This repo now includes a lightweight upstream-watch layer so CLAWG can track Hermes Agent safely.

## Goals

- watch `NousResearch/hermes-agent` regularly
- classify upstream changes before touching CLAWG
- protect CLAWG-only surfaces during merges
- support an external agentic cron that can perform the full merge + audit + PR flow

## What was added

### 1. `scripts/setup_hermes_upstream.sh`
Bootstraps the local repo for upstream sync:
- adds `upstream` remote if missing
- fetches `upstream/main`
- enables `git rerere`
- configures the `merge.clawg-ours` driver

Run once locally:

```bash
bash scripts/setup_hermes_upstream.sh
```

### 2. `.gitattributes`
Marks CLAWG-only surfaces to keep the CLAWG version during upstream syncs:
- `AGENTS.md`
- `README.md`
- `landingpage/**`
- `website/**`
- `subagents/**`
- `optional-skills/**`
- `dashboard/**`

### 3. `scripts/hermes_sync_report.py`
Produces a machine-readable risk report for incoming Hermes changes.

Example:

```bash
python scripts/hermes_sync_report.py --repo . --json-out /tmp/hermes.json --md-out /tmp/hermes.md
```

It reports:
- merge-base
- ahead / behind counts
- changed files from upstream since the merge-base
- high / medium / low risk buckets
- whether the update should be treated as important

### 4. `.github/workflows/hermes-upstream-watch.yml`
Every 3 days (and on manual trigger), GitHub Actions:
- fetches Hermes upstream
- generates the sync report
- publishes the markdown report into the Actions summary
- uploads JSON + markdown artifacts

## Recommended agentic flow

The scheduled autonomous agent should do this:

1. Run `bash scripts/setup_hermes_upstream.sh`
2. Run `python scripts/hermes_sync_report.py`
3. If there is no important update: stop and report no-op
4. If there is an important update:
   - create a branch like `sync/hermes-YYYYMMDD-<shortsha>` from `main`
   - merge `upstream/main`
   - use parallel subagents to audit:
     - upstream diff + merge risk
     - CLAWG rebranding / Second Brain / skills / Telegram surfaces
     - test execution + regression analysis
5. Only if the branch is safe:
   - run the relevant tests
   - push the branch
   - open or update a PR
6. Never push directly to `main`

## Suggested risk zones for the agent

Always treat these as manual-review zones even after a clean merge:
- `run_agent.py`
- `model_tools.py`
- `toolsets.py`
- `gateway/**`
- `clawg_cli/main.py`
- `clawg_cli/config.py`
- `clawg_cli/setup.py`
- `tools/browser_tool.py`
- `tools/mcp_tool.py`
- `tools/memory_tool.py`
- `scripts/install.*`
- `pyproject.toml`

## Why branch + PR instead of direct push

Even when automation is good, this repo has CLAWG-specific behavior:
- Second Brain prompt layer
- CLAWG branding
- CLAWG-only docs / subagents / dashboard
- custom tools like vault / honcho integrations

Branch + PR keeps the flow safe while still being highly automated.
