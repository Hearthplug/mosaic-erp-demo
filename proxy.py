import http.client, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UP = ('127.0.0.1', 8001)

def creds():
    try:
        return json.load(open('/tmp/demo_creds.json'))
    except Exception:
        return None

class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def _landing(self):
        c = creds()
        body = open(os.environ.get('LANDING_PATH','/app/landing.html'), encoding='utf-8').read()
        if c:
            ident = json.dumps({'workspace_id': c['wid'], 'user_id': 'owner', 'role': 'owner', 'workspace_name': c['name']})
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
