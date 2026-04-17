#!/bin/bash
# Double-click in Finder (may need: chmod +x run_dashboard.sh) or run: ./run_dashboard.sh
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"
VENV="$ROOT/.rlc_venv/bin/streamlit"
if [[ ! -x "$VENV" ]]; then
  echo "Missing venv. Run: python3 -m venv .rlc_venv && .rlc_venv/bin/pip install streamlit pandas"
  exit 1
fi
echo "Starting dashboard…"
echo "Open in your browser:  http://127.0.0.1:8501"
echo "Keep this window open while you view the site. Press Ctrl+C to stop."
exec "$VENV" run "$ROOT/app.py" --server.address 127.0.0.1 --server.port 8501
