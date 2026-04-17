#!/bin/bash
# Fallback if Streamlit won't start: plain HTTP + HTML charts
cd "$(dirname "$0")"
echo "Open:  http://127.0.0.1:8765/static_viewer.html"
echo "Press Ctrl+C to stop."
exec python3 -m http.server 8765 --bind 127.0.0.1
