#!/usr/bin/env bash
# sys-status.sh — KAIDO Homelab health check
# Intended as a no_agent cron job script, delivering to #sys-status.
# Reports disk, memory, uptime, Tailscale, services.

set -euo pipefail

HOST="$(hostname)"
UPTIME="$(uptime -p 2>/dev/null || echo 'N/A')"
LOAD="$(uptime 2>/dev/null | awk -F'load average:' '{print $2}' | xargs || echo 'N/A')"
NOW="$(date '+%Y-%m-%d %H:%M:%S')"

# ── Disk ──
DISK="$(df -h / /home 2>/dev/null | awk 'NR>1 {printf "  %-12s %5s used / %5s (%s)\n", $1, $3, $2, $5}')"

# ── Memory ──
MEM="$(free -h 2>/dev/null | awk '/Mem:/ {printf "  %-12s %5s used / %s\n", "RAM", $3, $2}')"
SWAP="$(free -h 2>/dev/null | awk '/Swap:/ {printf "  %-12s %5s used / %s\n", "Swap", $3, $2}')"

# ── Tailscale ──
TS="$(tailscale status 2>/dev/null | head -10 || echo '  ⚠️  Not connected or tailscale not found')"

# ── Services ──
SVC_OUT=""
for svc in hermes-gateway hermes-webui syncthing; do
  if systemctl --user is-active "$svc" &>/dev/null 2>&1; then
    SVC_OUT+="  ✅ $svc"$'\n'
  else
    SVC_OUT+="  ❌ $svc"$'\n'
  fi
done

# ── Output ──
cat <<EOF
🖥️ **KAIDO Homelab Health — $(date '+%A, %d %b %Y')**

**Host:** $HOST
**Uptime:** $UPTIME
**Load:** $LOAD

**💾 Disk:**
$DISK

**🧠 Memory:**
${MEM}
${SWAP}

**📡 Tailscale:**
$TS

**✅ Services:**
$SVC_OUT
⏱️ Refreshed: $NOW
EOF
