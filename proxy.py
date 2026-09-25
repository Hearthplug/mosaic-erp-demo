import http.client, json, os, sqlite3, hashlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UP = ('127.0.0.1', 8001)

def creds():
    try:
        return json.load(open('/tmp/demo_creds.json'))
    except Exception:
        return None


BANNERS = {
    '/interview': (b'<div style="box-sizing:border-box;width:100%;padding:8px 14px;background:#202522;color:#fff;'
                   b'font:13px/1.45 -apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif;'
                   b'border-left:4px solid #f26a3d">'
                   b'<b style="color:#f26a3d">Shared sample store.</b> Your answers here reconfigure the same shop '
                   b'every visitor sees. It resets every 6 hours - please skip real business details.</div>'),
    '/retail': (b'<div style="box-sizing:border-box;width:100%;padding:8px 14px;background:#202522;color:#fff;'
                b'font:13px/1.45 -apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif;'
                b'border-left:4px solid #f26a3d">'
                b'<b style="color:#f26a3d">Shared sample store.</b> This shop was configured by the last '
                b'visitor\'s interview answers - run the interview and it reshapes around yours. '
                b'Resets every 6 hours.</div>'),
    '/operations': (b'<div style="box-sizing:border-box;width:100%;padding:8px 14px;background:#202522;color:#fff;'
                    b'font:13px/1.45 -apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif;'
                    b'border-left:4px solid #f26a3d">'
                    b'<b style="color:#f26a3d">Shared sample store.</b> This shop was configured by the last '
                    b'visitor\'s interview answers - run the interview and it reshapes around yours. '
                    b'Resets every 6 hours.</div>'),
}

DB = os.environ.get('MOSAIC_DB_PATH', '/data/mosaic.db')

COUNTRY_CCY = [('india', 'INR'), ('united states', 'USD'), ('uae', 'AED'), ('united arab emirates', 'AED'),
               ('singapore', 'SGD'), ('china', 'CNY'), ('vietnam', 'VND'), ('malaysia', 'MYR'),
               ('united kingdom', 'GBP'), ('canada', 'CAD'), ('european union', 'EUR')]


def _canon(o):
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def _live_workspace_name(key):
    try:
        conn = http.client.HTTPConnection(*UP, timeout=5)
        conn.request('GET', '/api/workspace', headers={'Authorization': 'Bearer ' + key})
        r = conn.getresponse()
        data = json.loads(r.read())
        conn.close()
        if r.status == 200:
            return data.get('name')
    except Exception:
        pass
    return None


def _retarget_currency(auth_header, session_id):
    # Demo-only: after a visitor applies their interview, point the shared
    # shop's base currency at the country they described. Mirrors the app's
    # accounting.change_settings invariants so the books show an honest
    # invalidated-verification state afterwards.
    try:
        if not auth_header or not auth_header.startswith('Bearer '):
            return
        key = auth_header[7:]
        conn = http.client.HTTPConnection(*UP, timeout=15)
        conn.request('GET', '/api/onboarding/session?id=' + session_id,
                     headers={'Authorization': auth_header})
        r = conn.getresponse()
        payload = r.read()
        conn.close()
        if r.status != 200:
            return
        answers = json.loads(payload).get('answers', {})
        country = (answers.get('country') or '').lower()
        ccy = next((v for k, v in COUNTRY_CCY if k in country), None)
        if not ccy:
            return
        db = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
        sess = db.execute('SELECT workspace_id FROM onboarding_sessions WHERE id=?', (session_id,)).fetchone()
        if not sess:
            db.close()
            return
        wid = sess['workspace_id']
        old = db.execute('SELECT base_currency, fiscal_year_start FROM accounting_settings WHERE workspace_id=?', (wid,)).fetchone()
        if not old or old['base_currency'] == ccy:
            db.close()
            return
        actor = db.execute('SELECT id FROM api_keys WHERE workspace_id=? AND key_hash=?', (wid, hashlib.sha256(key.encode()).hexdigest())).fetchone()
        actor_id = actor['id'] if actor else 'demo-proxy'
        now = datetime.now(timezone.utc).isoformat()
        merged = {'base_currency': ccy, 'fiscal_year_start': old['fiscal_year_start']}
        db.execute("UPDATE accounting_settings SET base_currency=?, config_version=config_version+1, config_hash=?, verification_state='invalidated', invalidated_at=?, invalidation_reason=? WHERE workspace_id=?",
                   (ccy, hashlib.sha256(_canon(merged).encode()).hexdigest(), now, 'base_currency', wid))
        db.execute('INSERT INTO audit_events(workspace_id,at,actor_key_id,action,detail_json) VALUES(?,?,?,?,?)',
                   (wid, now, actor_id, 'accounting.material_change', _canon({'changes': {'base_currency': ccy}, 'verification_invalidated': True, 'source': 'demo.apply'})))
        db.commit()
        db.close()
    except Exception:
        return


class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def _landing(self):
        c = creds()
        body = open(os.environ.get('LANDING_PATH','/app/landing.html'), encoding='utf-8').read()
        if c:
            ident = json.dumps({'workspace_id': c['wid'], 'user_id': 'owner', 'role': 'owner', 'workspace_name': _live_workspace_name(c['key']) or c['name']})
            body = body.replace('__KEY__', c['key']).replace('__IDENT__', ident)
        else:
            body = body.replace('__KEY__', '').replace('__IDENT__', '{}')
        b = body.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(b)


    def _google_verification(self):
        b = b'google-site-verification: google1cac9f269019bde5.html'
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        self.wfile.write(b)

    def _proxy(self, upstream_path):
        n = int(self.headers.get('Content-Length') or 0)
        data = self.rfile.read(n) if n else None
        conn = http.client.HTTPConnection(*UP, timeout=120)
        hdrs = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'content-length', 'connection')}
        conn.request(self.command, upstream_path, body=data, headers=hdrs)
        r = conn.getresponse()
        payload = r.read()
        if self.command == 'POST' and upstream_path == '/api/onboarding/apply' and r.status == 200:
            try:
                sid = json.loads(data or b'{}').get('id', '')
                if sid:
                    _retarget_currency(self.headers.get('Authorization', ''), sid)
            except Exception:
                pass
        if self.command == 'GET' and upstream_path in BANNERS and 'text/html' in dict(r.getheaders()).get('Content-Type', ''):
            payload = payload.replace(b'<body>', b'<body>' + BANNERS[upstream_path], 1)
        self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() in ('transfer-encoding', 'connection', 'content-length'):
                continue
            self.send_header(k, v)
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        conn.close()

    def _route(self):
        path = self.path.split('?', 1)[0]
        if path == '/':
            return self._landing()
        if path == '/google1cac9f269019bde5.html':
            return self._google_verification()
        if path == '/signin':
            qs = self.path.split('?', 1)[1] if '?' in self.path else ''
            nxt = ''
            for part in qs.split('&'):
                if part.startswith('next=') and part[5:].startswith('%2F'):
                    nxt = '?next=' + part[5:]
                    break
            target = '/' + nxt
            b = b''
            self.send_response(302)
            self.send_header('Location', target)
            self.send_header('Content-Length', '0')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(b)
            return
        if path == '/today':
            qs = ('?' + self.path.split('?', 1)[1]) if '?' in self.path else ''
            return self._proxy('/' + qs)
        return self._proxy(self.path)

    do_GET = do_POST = do_PUT = do_DELETE = _route

ThreadingHTTPServer(('0.0.0.0', 8000), H).serve_forever()
