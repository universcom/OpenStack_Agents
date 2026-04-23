#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# run.sh — Start the OpenStack AI Agent backend and frontend together.
#
# Usage:
#   ./run.sh              # default: server on :8080, UI on :5173
#   ./run.sh --port 9090  # custom backend port (frontend still on :5173)
#
# Press Ctrl-C once to stop both processes cleanly.
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Resolve project root (works regardless of where the script is called from) ─
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Colour helpers ─────────────────────────────────────────────────────────────
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'
RESET='\033[0m'

log()    { echo -e "${DIM}[run.sh]${RESET} $*"; }
info()   { echo -e "${CYAN}[run.sh]${RESET} $*"; }
ok()     { echo -e "${GREEN}[run.sh]${RESET} $*"; }
warn()   { echo -e "${YELLOW}[run.sh]${RESET} $*"; }
err()    { echo -e "${RED}[run.sh]${RESET} $*" >&2; }

# ── Argument parsing ───────────────────────────────────────────────────────────
BACKEND_PORT=8080

while [[ $# -gt 0 ]]; do
  case $1 in
    --port|-p) BACKEND_PORT="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $0 [--port PORT]"
      echo "  --port PORT   Backend server port (default: 8080)"
      exit 0
      ;;
    *) err "Unknown argument: $1"; exit 1 ;;
  esac
done

# ── Validate prerequisites ─────────────────────────────────────────────────────

# Python virtual environment
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  err "Virtual environment not found at .venv/"
  err "Run:  python -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

# Node / npm for the frontend
if ! command -v npm &>/dev/null; then
  err "npm not found. Install Node.js from https://nodejs.org"
  exit 1
fi

# Frontend dependencies
FRONTEND_DIR="$ROOT/frontend"
if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  info "Frontend dependencies not installed — running npm install…"
  npm --prefix "$FRONTEND_DIR" install
fi

# ── PID tracking (used by the cleanup trap) ────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  info "Shutting down…"
  [[ -n "$BACKEND_PID"  ]] && kill "$BACKEND_PID"  2>/dev/null && log "Backend stopped  (PID $BACKEND_PID)"
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null && log "Frontend stopped (PID $FRONTEND_PID)"
  ok "All processes stopped. Goodbye."
  exit 0
}

# Trap Ctrl-C (SIGINT) and normal exit so cleanup always runs.
trap cleanup SIGINT SIGTERM EXIT

# ── Banner ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}┌─────────────────────────────────────────────────┐${RESET}"
echo -e "${CYAN}│        OpenStack AI Agent — Dev Launcher        │${RESET}"
echo -e "${CYAN}└─────────────────────────────────────────────────┘${RESET}"
echo ""

# ── Start backend ──────────────────────────────────────────────────────────────
info "Starting backend on http://localhost:${BACKEND_PORT} …"

# Prefix each backend log line with a cyan [API] tag so it's easy to distinguish
# from frontend output when both stream to the same terminal.
"$PYTHON" "$ROOT/main.py" --mode server --port "$BACKEND_PORT" 2>&1 \
  | sed "s/^/$(printf "${CYAN}[API]${RESET} ")/" &

BACKEND_PID=$!
log "Backend PID: $BACKEND_PID"

# Give the server a moment to bind its port before the frontend starts.
# This avoids the UI showing "Disconnected" on the very first health check.
sleep 1

# Check the backend actually started (non-zero exit in the first second = bad).
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  err "Backend failed to start. Check the output above."
  exit 1
fi

# ── Start frontend ─────────────────────────────────────────────────────────────
info "Starting frontend on http://localhost:5173 …"

# Prefix each frontend log line with a green [UI] tag.
npm --prefix "$FRONTEND_DIR" run dev 2>&1 \
  | sed "s/^/$(printf "${GREEN}[UI]${RESET}  ")/" &

FRONTEND_PID=$!
log "Frontend PID: $FRONTEND_PID"

# ── Ready message ──────────────────────────────────────────────────────────────
sleep 2
echo ""
ok "Both services are running:"
echo -e "  ${CYAN}Backend API${RESET}  →  http://localhost:${BACKEND_PORT}"
echo -e "  ${GREEN}Frontend UI${RESET}  →  http://localhost:5173"
echo ""
warn "Press Ctrl-C to stop both."
echo ""

# ── Wait — keep the script alive until a process exits or Ctrl-C ───────────────
# 'wait -n' returns when ANY background job exits (bash 4.3+).
# On older bash (macOS default), fall back to polling.
if wait -n 2>/dev/null; then
  err "One of the services exited unexpectedly."
else
  # Polling fallback for bash < 4.3 (macOS ships bash 3.x by default).
  while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
    sleep 2
  done
  err "One of the services exited unexpectedly."
fi

exit 1
