FROM ghcr.io/hearthplug/mosaic-erp:1.4.1
COPY --chown=10001:10001 interview.html interview.css interview.js operations.html operations.js operations.css /app/
COPY --chown=10001:10001 start.sh seed.py proxy.py landing.html /app/
ENTRYPOINT ["/bin/sh", "/app/start.sh"]
