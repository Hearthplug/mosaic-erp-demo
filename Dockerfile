FROM ghcr.io/hearthplug/mosaic-erp:2.1.2
COPY --chown=10001:10001 start.sh seed.py proxy.py landing.html cleanup_drafts.py /app/
ENTRYPOINT ["/bin/sh", "/app/start.sh"]
