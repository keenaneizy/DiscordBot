"""
Tiny Flask web server so free-tier Render — which only supports Web
Services, not standalone background workers — has a port to bind to and a
health-check route an uptime pinger can hit. Not needed on Railway.

Only started when RENDER_KEEP_ALIVE=1 is set (see bot.py + README.md).
"""
import os
from threading import Thread

from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Phantom Picks bot is running 👻"


def _run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    thread = Thread(target=_run, daemon=True)
    thread.start()
