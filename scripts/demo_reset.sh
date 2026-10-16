#!/usr/bin/env bash
# One command before the demo (Git Bash, repo root):  bash scripts/demo_reset.sh
# Stops the hub on :8443, rebuilds data/demo/ (SYNTHETIC DEMO DATA), starts the hub on data/demo/
# and prints the phone URL that loads the demo persona. data/apna.db is never touched.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
PY="$ROOT/backend/.venv/Scripts/python"
PORT=8443

PID=$(netstat -ano | grep ":$PORT " | grep LISTEN | awk '{print $5}' | head -1 || true)
if [ -n "${PID:-}" ] && [ "$PID" != "0" ]; then
  echo "Stopping the hub on :$PORT (PID $PID)"
  taskkill //PID "$PID" //F >/dev/null
  sleep 2
fi

"$PY" scripts/seed_demo.py --reset

mkdir -p models
cd backend
DATA_DIR=data/demo PORT=$PORT nohup "$PY" -m app.main > ../models/hub_demo.log 2>&1 &
cd "$ROOT"

echo -n "Waiting for the hub"
for _ in $(seq 1 60); do
  if curl -sk "https://localhost:$PORT/api/health" | grep -q '"ok":true'; then echo " up"; break; fi
  echo -n "."; sleep 1
done
curl -sk "https://localhost:$PORT/api/health" | grep -q '"ok":true' || { echo; echo "Hub did not start; see models/hub_demo.log"; exit 1; }

IP=$("$PY" -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('10.255.255.255', 1)); print(s.getsockname()[0])" 2>/dev/null || echo "<LAN-IP>")
echo
echo "Demo hub running on data/demo (log: models/hub_demo.log)"
echo "Open on the phone:  https://$IP:$PORT/?demo=demo-sunita"
echo "Back to real data later: stop the hub and start it without DATA_DIR."
