#!/usr/bin/env bash
# vault-backup.sh — Auto-commit and push vault to GitHub
# Runs daily at 05:00 via cron. Silent when nothing to commit.
set -euo pipefail

VAULT="$HOME/vault"
cd "$VAULT"

# Stage all changes
git add -A

# Only commit if there's something to commit
if git diff --cached --quiet; then
  echo "vault-backup: nothing to commit at $(date --iso-8601=seconds)"
  exit 0
fi

git commit -m "auto-backup $(date +%Y-%m-%d)"
echo "vault-backup: committed at $(date --iso-8601=seconds)"

# Push to GitHub — detect default branch dynamically (main or master)
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}')
DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}
git push origin "$DEFAULT_BRANCH" 2>&1 && echo "vault-backup: pushed to GitHub ($DEFAULT_BRANCH)" || echo "vault-backup: push failed (check remote)"
