FROM ghcr.io/hearthplug/mosaic-erp:1.4.1
COPY --chown=10001:10001 start.sh seed.py proxy.py landing.html /app/
ENTRYPOINT ["/bin/sh", "/app/start.sh"]
