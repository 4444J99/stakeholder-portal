#!/usr/bin/env bash
set -euo pipefail

# Setup script for mobile access to the ORGANVM dashboard.
# Installs LaunchAgents for the dashboard and cloudflared tunnel.
#
# Prerequisites:
#   - cloudflared installed (brew install cloudflared)
#   - cloudflared tunnel already created and DNS routed
#   - ~/.cloudflared/config.yml configured
#   - ORGANVM_API_KEY stored in Keychain

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LOGS_DIR="$HOME/System/Logs"

echo "==> Setting up ORGANVM mobile access"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Load API key into environment for the dashboard LaunchAgent
API_KEY=$(security find-generic-password -s "organvm-api-key" -w 2>/dev/null || echo "")
if [[ -z "$API_KEY" ]]; then
    echo "WARNING: No API key found in Keychain (service: organvm-api-key)"
    echo "  Generate one: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
    echo "  Store it: security add-generic-password -a \"\$USER\" -s \"organvm-api-key\" -w \"<key>\""
fi

# Install dashboard LaunchAgent
echo "==> Installing dashboard LaunchAgent"
DASHBOARD_PLIST="$LAUNCH_AGENTS_DIR/com.4jp.organvm.dashboard.plist"
if launchctl list com.4jp.organvm.dashboard &>/dev/null; then
    launchctl unload "$DASHBOARD_PLIST" 2>/dev/null || true
fi
cp "$SCRIPT_DIR/com.4jp.organvm.dashboard.plist" "$DASHBOARD_PLIST"

# Inject API key into the plist if available
if [[ -n "$API_KEY" ]]; then
    # Add ORGANVM_API_KEY to the EnvironmentVariables dict
    /usr/libexec/PlistBuddy -c "Add :EnvironmentVariables:ORGANVM_API_KEY string $API_KEY" "$DASHBOARD_PLIST" 2>/dev/null \
        || /usr/libexec/PlistBuddy -c "Set :EnvironmentVariables:ORGANVM_API_KEY $API_KEY" "$DASHBOARD_PLIST"
    echo "  API key injected into LaunchAgent"
fi

launchctl load "$DASHBOARD_PLIST"
echo "  Dashboard LaunchAgent loaded (http://localhost:8000)"

# Install cloudflared LaunchAgent
echo "==> Installing cloudflared LaunchAgent"
TUNNEL_PLIST="$LAUNCH_AGENTS_DIR/com.4jp.cloudflared.organvm.plist"
if launchctl list com.4jp.cloudflared.organvm &>/dev/null; then
    launchctl unload "$TUNNEL_PLIST" 2>/dev/null || true
fi
cp "$SCRIPT_DIR/com.4jp.cloudflared.organvm.plist" "$TUNNEL_PLIST"
launchctl load "$TUNNEL_PLIST"
echo "  Cloudflared LaunchAgent loaded"

# Verify
echo ""
echo "==> Verification"
sleep 2
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/api | grep -q 200; then
    echo "  Dashboard: OK (http://localhost:8000)"
else
    echo "  Dashboard: NOT YET READY (may take a few seconds to start)"
fi

echo ""
echo "==> Setup complete!"
echo ""
echo "API key for iOS Shortcuts:"
if [[ -n "$API_KEY" ]]; then
    echo "  $API_KEY"
else
    echo "  (not configured — see warning above)"
fi
echo ""
echo "Test from phone (after tunnel is active):"
echo "  curl -H 'X-API-Key: <key>' https://dash.ivixivi.xyz/api/v1/status"  # allow-secret
