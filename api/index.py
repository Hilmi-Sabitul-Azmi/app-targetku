# Entry point untuk Vercel (serverless function).
# Vercel mencari variabel bernama "app" yang merupakan WSGI application.
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app  # noqa: E402
