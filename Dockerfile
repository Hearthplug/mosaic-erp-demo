FROM ghcr.io/hearthplug/mosaic-erp:2.0.0
COPY --chown=10001:10001 interview.html interview.css operations.html operations.css /app/
COPY --chown=10001:10001 auth.js accounting.js assist.js assistant.js build.js close.js interview.js migration.js operations.js retail.js static.js voice.js /app/
COPY --chown=10001:10001 start.sh seed.py proxy.py landing.html /app/
ENTRYPOINT ["/bin/sh", "/app/start.sh"]
