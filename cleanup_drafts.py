"""Demo hygiene: visitors share one seeded workspace between 6-hour reseeds,
so their Build drafts would pile up for everyone else. Sweep visitor drafts
older than 30 minutes; keep the seeded review draft and anything active."""
import sqlite3
from datetime import datetime, timedelta, timezone

KEEP = 'Supplier bills - Golden Grains Co.'
cutoff = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
db = sqlite3.connect('/data/mosaic.db')
cur = db.execute(
    "DELETE FROM generated_artifacts WHERE status='draft' AND name != ? AND created_at < ?",
    (KEEP, cutoff))
db.commit()
print('swept', cur.rowcount, 'visitor drafts')
db.close()
