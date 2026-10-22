#!/usr/bin/env bash
# Production-mode demo: Next.js build plus the API, both on 0.0.0.0.
# Dev mode blocks some requests from other devices; this does not.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

lan_ip() {
  local ip=""
  for iface in en0 en1 en2 bridge0; do
    ip="$(ipconfig getifaddr "$iface" 2>/dev/null || true)"
    if [[ -n "$ip" ]]; then
      echo "$ip"
      return
    fi
  done
  python3 - <<'PY'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("8.8.8.8", 80))
    print(s.getsockname()[0])
except OSError:
    print("127.0.0.1")
finally:
    s.close()
PY
}

IP="$(lan_ip)"
echo "Building the web app…"
(cd "$ROOT/frontend" && npx next build)
cd "$ROOT/backend"
RUN_MAINTENANCE=true uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
cd "$ROOT/frontend"
npx next start --hostname 0.0.0.0 --port 3000 &
WEB_PID=$!
cleanup() { kill "$API_PID" "$WEB_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

echo
echo "Bazaar is ready. Password for every demo account is: demo"
echo "  This machine     http://127.0.0.1:3000"
echo "  Other devices    http://${IP}:3000"
echo "  Swagger          http://${IP}:3000/api/docs"
echo "  API directly     http://${IP}:8000/api/docs"
echo
wait
