"""Throwaway UX prototype: python3 apps/web/prototype/serve.py"""
import os
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

if os.environ.get('NODE_ENV') == 'production':
    raise SystemExit('This throwaway prototype is disabled in production.')

os.chdir(Path(__file__).parent)
print('UX prototype: http://127.0.0.1:4317/?variant=A', flush=True)
ThreadingHTTPServer(('127.0.0.1', 4317), SimpleHTTPRequestHandler).serve_forever()
