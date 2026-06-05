#!/usr/bin/env bash
# sys-status.sh — System health snapshot
# Runs every 4h via cron. Output to Discord #sys-status.
set -euo pipefail

{
  echo "🖥️ **KAIDO-01 Status — $(date '+%Y-%m-%d %H:%M')**"
  echo ""

  echo "**Uptime:** $(uptime -p)"\
  echo ""

  echo "**Disk:**"
  df -h / /home 2>/dev/null | tail -n +2 | while read -r line; do
    echo "- $line"
  done
  echo ""

  echo "**Memory:**"
  free -h | tail -n +2 | while read -r line; do
    echo "- $line"
  done
  echo ""

  echo "**Services:**"
  for svc in hermes-gateway hermes-webui syncthing; do
    status=$(systemctl --user is-active "$svc" 2>/dev/null || echo "inactive")
    icon="✅"
    [ "$status" != "active" ] && icon="❌"
    echo "- $icon $svc ($status)"
  done
  echo ""

  if command -v tailscale &>/dev/null; then
    echo "**Tailscale:**"
    tailscale status 2>/dev/null | head -5 || echo "- not connected"
  fi
} 2>&1
