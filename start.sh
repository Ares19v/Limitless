#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}"
echo "  ██████╗  ██████╗  ██████╗██╗   ██╗███╗   ███╗██╗███╗   ██╗██████╗ "
echo "  ██╔══██╗██╔═══██╗██╔════╝██║   ██║████╗ ████║██║████╗  ██║██╔══██╗"
echo "  ██║  ██║██║   ██║██║     ██║   ██║██╔████╔██║██║██╔██╗ ██║██║  ██║"
echo "  ██║  ██║██║   ██║██║     ██║   ██║██║╚██╔╝██║██║██║╚██╗██║██║  ██║"
echo "  ██████╔╝╚██████╔╝╚██████╗╚██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██████╔╝"
echo "  ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝"
echo -e "${NC}"
echo "  AI-Powered PDF Chat  --  Production Ready"
echo "  =========================================="
echo ""

# ── Check Python ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}[ERROR] Python3 not found. Install from python.org${NC}"; exit 1
fi

# ── Check Node ────────────────────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
  echo -e "${RED}[ERROR] Node.js not found. Install from nodejs.org${NC}"; exit 1
fi

# ── Setup .env files ──────────────────────────────────────────────────────────
if [ ! -f "$BACKEND_DIR/.env" ]; then
  echo -e "${YELLOW}[SETUP] Creating backend .env from example...${NC}"
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  echo -e "${YELLOW}[!] IMPORTANT: Edit backend/.env and add your API keys.${NC}"
fi

if [ ! -f "$FRONTEND_DIR/.env" ]; then
  cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
fi

# ── Backend virtual environment ───────────────────────────────────────────────
if [ ! -d "$BACKEND_DIR/.venv" ]; then
  echo -e "${GREEN}[SETUP] Creating Python virtual environment...${NC}"
  python3 -m venv "$BACKEND_DIR/.venv"
  echo -e "${GREEN}[SETUP] Installing backend dependencies...${NC}"
  "$BACKEND_DIR/.venv/bin/pip" install -q -r "$BACKEND_DIR/requirements.txt"
fi

# ── Frontend dependencies ─────────────────────────────────────────────────────
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo -e "${GREEN}[SETUP] Installing frontend dependencies...${NC}"
  cd "$FRONTEND_DIR" && npm install --silent && cd "$SCRIPT_DIR"
fi

echo ""
echo -e "${GREEN}  Starting services...${NC}"
echo "  Backend  -> http://localhost:8000  (Docs: http://localhost:8000/docs)"
echo "  Frontend -> http://localhost:5173"
echo ""

# ── Start services ────────────────────────────────────────────────────────────
# Backend
"$BACKEND_DIR/.venv/bin/uvicorn" app.main:app \
  --host 0.0.0.0 --port 8000 --reload \
  --app-dir "$BACKEND_DIR" &
BACKEND_PID=$!

# Frontend
cd "$FRONTEND_DIR" && npm run dev &
FRONTEND_PID=$!

# ── Open browser after delay ──────────────────────────────────────────────────
sleep 3
open "http://localhost:5173" 2>/dev/null || xdg-open "http://localhost:5173" 2>/dev/null || true

echo -e "${GREEN}[OK] Limitless is running!${NC}"
echo "  Press Ctrl+C to stop all services."

# ── Graceful shutdown ─────────────────────────────────────────────────────────
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'; exit 0" INT TERM
wait $BACKEND_PID $FRONTEND_PID
