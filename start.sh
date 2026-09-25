#!/bin/sh
set -e
export MOSAIC_HOST=127.0.0.1 PORT=8001 MOSAIC_DB_PATH=/data/mosaic.db
RESET="${RESET_SECONDS:-21600}"
while true; do
  rm -f /data/mosaic.db /tmp/demo_creds.json
  python /app/app.py serve &
  APP=$!
  ok=""
  i=0
  while [ $i -lt 60 ]; do
    if python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8001/health/ready',timeout=2)" 2>/dev/null; then ok=1; break; fi
    i=$((i+1)); sleep 2
  done
  [ -n "$ok" ] && python /app/seed.py
  python /app/proxy.py &
  PROXY=$!
  ( while true; do sleep 900; python /app/cleanup_drafts.py || true; done ) &
  CLEAN=$!
  sleep "$RESET"
  kill $PROXY $APP $CLEAN 2>/dev/null || true
  wait $PROXY 2>/dev/null || true
  wait $APP 2>/dev/null || true
done
