#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# set-github-secrets.sh
# Reads every KEY=VALUE from ../.env and pushes each one as a GitHub secret.
#
# Requirements:
#   - GitHub CLI installed: brew install gh
#   - Logged in:           gh auth login
#
# Usage (from repo root):
#   bash scripts/set-github-secrets.sh
#
# The script skips blank lines and comment lines (# ...).
# It will NOT push VITE_* vars — those are baked in at build time via the
# VITE_API_BASE_URL secret you already set separately.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ENV_FILE="$(dirname "$0")/../.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE"
  exit 1
fi

# Detect repo from git remote automatically
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
if [[ -z "$REPO" ]]; then
  echo "ERROR: Could not detect GitHub repo. Run from inside the repo folder."
  exit 1
fi

echo "Setting secrets for repo: $REPO"
echo ""

while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip blank lines and comments
  [[ -z "$line" || "$line" == \#* ]] && continue

  # Split on first '='
  KEY="${line%%=*}"
  VALUE="${line#*=}"

  # Skip VITE_ vars — those are build-time only
  if [[ "$KEY" == VITE_* ]]; then
    echo "  skipping (build-time): $KEY"
    continue
  fi

  gh secret set "$KEY" --body "$VALUE" --repo "$REPO"
  echo "  ✓ $KEY"
done < "$ENV_FILE"

echo ""
echo "Done. All .env secrets pushed to GitHub."