#!/usr/bin/env bash
#
# Last30Days Pro Max — one-step MCP setup
# Wires the listening-engine MCP server into Claude Code and/or Claude Desktop
# so anyone (Marketing, Product, eng) can run competitor reports by just chatting.
#
# Usage:
#   ./setup.sh                 # interactive (prompts for an optional Zyte key)
#   ZYTE_API_KEY=xxx ./setup.sh # non-interactive (key taken from the environment)
#
# Re-running is safe: it replaces any previous registration.

set -euo pipefail

BOLD=$'\033[1m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; DIM=$'\033[2m'; NC=$'\033[0m'
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_NAME="last30days"

say()  { printf "%s\n" "$*"; }
ok()   { printf "${GREEN}✓${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}!${NC} %s\n" "$*"; }
die()  { printf "${RED}✗ %s${NC}\n" "$*" >&2; exit 1; }

say "${BOLD}Last30Days Pro Max — MCP setup${NC}"
say "${DIM}repo: ${REPO}${NC}"
say ""

# 1. Prerequisites -----------------------------------------------------------
command -v python3 >/dev/null 2>&1 || die "python3 not found. Install Python 3.9+ and re-run."
PYTHONPATH="$REPO" python3 -c "import last30days_pro_max" 2>/dev/null \
  || die "Could not import the package from $REPO. Run this script from inside the project folder."
ok "Python and package import OK ($(python3 --version 2>&1))"

# 2. Zyte API key (optional — only needed for LIVE web data) -----------------
KEY="${ZYTE_API_KEY:-}"
if [ -z "$KEY" ] && [ -t 0 ]; then
  say ""
  say "Enter your ${BOLD}Zyte API key${NC} for live web data, or press Enter to skip"
  say "${DIM}(skip = mock mode only, which is free and needs no key)${NC}"
  printf "Zyte API key: "
  read -rs KEY || true
  say ""
fi
if [ -n "$KEY" ]; then ok "Zyte key provided — LIVE mode enabled"; else warn "No key — MOCK mode only (you can re-run later with a key)"; fi

# 3. Register with Claude Code ----------------------------------------------
if command -v claude >/dev/null 2>&1; then
  claude mcp remove "$SERVER_NAME" >/dev/null 2>&1 || true
  if [ -n "$KEY" ]; then
    claude mcp add "$SERVER_NAME" \
      -e "PYTHONPATH=$REPO" -e "ZYTE_API_KEY=$KEY" \
      -- python3 -m last30days_pro_max.mcp_server >/dev/null
  else
    claude mcp add "$SERVER_NAME" \
      -e "PYTHONPATH=$REPO" \
      -- python3 -m last30days_pro_max.mcp_server >/dev/null
  fi
  if claude mcp list 2>/dev/null | grep -q "$SERVER_NAME"; then
    ok "Registered with Claude Code (restart Claude Code to load the tools)"
  else
    warn "Added to Claude Code but could not confirm connection — check 'claude mcp list'"
  fi
else
  warn "Claude Code CLI ('claude') not found — skipping Claude Code setup"
fi

# 4. Register with Claude Desktop (safe JSON merge) -------------------------
case "$(uname -s)" in
  Darwin) DESKTOP_CFG="$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
  Linux)  DESKTOP_CFG="$HOME/.config/Claude/claude_desktop_config.json" ;;
  *)      DESKTOP_CFG="" ;;
esac
if [ -n "$DESKTOP_CFG" ] && [ -d "$(dirname "$DESKTOP_CFG")" ]; then
  REPO="$REPO" KEY="$KEY" CFG="$DESKTOP_CFG" python3 - <<'PY'
import json, os
cfg_path, repo, key = os.environ["CFG"], os.environ["REPO"], os.environ["KEY"]
data = {}
if os.path.exists(cfg_path):
    try: data = json.load(open(cfg_path))
    except Exception: data = {}
env = {"PYTHONPATH": repo}
if key: env["ZYTE_API_KEY"] = key
data.setdefault("mcpServers", {})["last30days"] = {
    "command": "python3",
    "args": ["-m", "last30days_pro_max.mcp_server"],
    "env": env,
}
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
json.dump(data, open(cfg_path, "w"), indent=2)
print("  desktop config updated:", cfg_path)
PY
  ok "Registered with Claude Desktop (restart Claude Desktop to load the tools)"
else
  warn "Claude Desktop not detected — skipping (install it, then re-run to add it)"
fi

# 5. Smoke test (mock, no key needed) ---------------------------------------
SMOKE="$(printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_report","arguments":{"mock":true,"query_limit":1}}}' \
  | PYTHONPATH="$REPO" python3 -m last30days_pro_max.mcp_server 2>/dev/null || true)"
if printf "%s" "$SMOKE" | grep -q "Last30Days Pro Max"; then
  ok "Smoke test passed — the server runs and returns a report"
else
  warn "Smoke test did not confirm output — try running the server manually to debug"
fi

# 6. Done -------------------------------------------------------------------
say ""
say "${BOLD}${GREEN}Setup complete.${NC}"
say ""
say "${BOLD}Next:${NC} restart Claude Code or Claude Desktop, then just ask in plain English:"
say "  ${DIM}• \"Run a mock listening report\"  (free, instant — try this first)${NC}"
say "  ${DIM}• \"Run a competitor report on Firecrawl and summarize their agent positioning\"${NC}"
say "  ${DIM}• \"What 'X vs Apify' content exists, and where's the gap for Zyte?\"${NC}"
say "  ${DIM}• \"Turn that into a PDF for the team\"${NC}"
say ""
[ -z "$KEY" ] && say "${DIM}(Live web data needs a Zyte key — re-run with: ZYTE_API_KEY=xxx ./setup.sh)${NC}"
exit 0
