# Termius Setup for ORGANVM

SSH into your Mac to run `organvm` CLI commands and `curl` the dashboard API.

## Connection Options

### A: LAN (any device)

SSH to your Mac's local IP on port 22.

**Prerequisites:** System Settings → General → Sharing → Remote Login → ON

**Termius host config:**
- Label: `organvm-lan`
- Address: `<Mac's local IP>` (find with `ipconfig getifaddr en0`)
- Port: `22`
- Username: `4jp`
- Authentication: Key (use 1Password SSH agent key)

### B: Remote (macOS/desktop Termius)

SSH via Cloudflare tunnel using `cloudflared access ssh` as a ProxyCommand.

**~/.ssh/config entry:**
```
Host organvm
    HostName ssh.ivixivi.xyz
    User 4jp
    ProxyCommand /opt/homebrew/bin/cloudflared access ssh --hostname %h
```

**Termius host config:**
- Label: `organvm`
- Address: `ssh.ivixivi.xyz`
- Username: `4jp`
- ProxyCommand: `/opt/homebrew/bin/cloudflared access ssh --hostname %h`

Then `ssh organvm` works from any network.

### C: Remote (iOS Termius)

Termius on iOS cannot run `cloudflared access ssh` as a ProxyCommand. Two options:

**Option 1: Cloudflare WARP (recommended)**
1. Install Cloudflare WARP on iPhone (App Store: "1.1.1.1")
2. Open WARP → Settings → Account → Login to Cloudflare Zero Trust
3. Enter your Zero Trust org name
4. Authenticate via browser
5. Enable WARP (toggle on)
6. In Termius, create host pointing to Mac's **private IP** — traffic routes through the WARP tunnel

**Option 2: LAN only**
- Use option A when on the same network as your Mac

## Shell Environment

After SSH, activate the workspace venv:
```bash
source ~/Workspace/meta-organvm/.venv/bin/activate
```

Or use the full path directly:
```bash
~/Workspace/meta-organvm/.venv/bin/organvm status
```

## Snippet Library

Create these as snippets in Termius. Group them under the tag **ORGANVM**.

### CLI Snippets (run after SSH)

| Name | Command |
|------|---------|
| `ov-status` | `organvm status --json \| python3 -m json.tool` |
| `ov-omega` | `organvm omega status` |
| `ov-registry` | `organvm registry list --organ {{ORGAN}}` |
| `ov-audit` | `organvm governance audit` |
| `ov-ci` | `organvm ci health` |
| `ov-deadlines` | `organvm deadlines --days {{DAYS}}` |
| `ov-seed` | `organvm seed validate` |
| `ov-metrics` | `organvm metrics calculate` |

### API Snippets (curl with plain-text output)

| Name | Command |
|------|---------|
| `ov-api-status` | `curl -sH 'Accept: text/plain' http://localhost:8000/api/v1/status` |
| `ov-api-omega` | `curl -sH 'Accept: text/plain' http://localhost:8000/api/v1/omega` |
| `ov-api-registry` | `curl -sH 'Accept: text/plain' 'http://localhost:8000/api/v1/registry?organ={{ORGAN}}'` |
| `ov-api-audit` | `curl -sH 'Accept: text/plain' http://localhost:8000/api/v1/governance/audit` |
| `ov-api-ci` | `curl -sH 'Accept: text/plain' http://localhost:8000/api/v1/ci` |
| `ov-api-deadlines` | `curl -sH 'Accept: text/plain' 'http://localhost:8000/api/v1/deadlines?days={{DAYS}}'` |
| `ov-api-board` | `curl -sH 'Accept: text/plain' http://localhost:8000/api/v1/coordination/board` |

When SSH'd to the Mac, these hit `localhost:8000` directly — no API key needed.

### Creating Snippets in Termius

1. Open Termius → Snippets
2. Tap **+** → New Snippet
3. Enter name (e.g., `ov-status`) and command
4. Use `{{VARIABLE}}` syntax for Termius variables — Termius prompts for values at runtime
5. Tag with **ORGANVM** for organization

## Remote API (via tunnel, with auth)

From any device outside the LAN:
```bash
curl -sH 'Accept: text/plain' \
     -H "X-API-Key: YOUR_KEY" \
     https://dash.ivixivi.xyz/api/v1/status
```

## Tips

- **Live dashboard in terminal:** `watch -n 30 'organvm status'`
- **Quick system check:** `ssh organvm 'organvm omega status'` (one-shot command)
- **JSON still works:** Omit the `Accept: text/plain` header to get JSON output
- **Plain-text is 60 columns wide** — fits Termius on iPhone in portrait mode
- **Pipe-safe:** Plain-text uses Unicode box-drawing, no ANSI colors — safe for `pbcopy`, files, and sharing
