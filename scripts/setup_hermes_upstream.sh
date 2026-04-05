#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UPSTREAM_URL="${1:-https://github.com/NousResearch/hermes-agent.git}"

cd "$REPO_ROOT"

if git remote get-url upstream >/dev/null 2>&1; then
  echo "upstream remote already configured: $(git remote get-url upstream)"
else
  git remote add upstream "$UPSTREAM_URL"
  echo "added upstream remote: $UPSTREAM_URL"
fi

git config rerere.enabled true
git config rerere.autoupdate true
git config merge.clawg-ours.name "Keep CLAWG custom version"
git config merge.clawg-ours.driver true

echo "configured git rerere + clawg-ours merge driver"

git fetch upstream main --prune

echo "upstream/main fetched successfully"
