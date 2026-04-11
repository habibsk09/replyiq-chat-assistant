"""
app.py — Flask entry point for the Chat Response Quality & Empathy Assistant
Registers all routes and starts the development server.
"""

from flask import Flask
from routes import register_routes

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["DEBUG"] = True  # flip to False in production

# ── register all API + page routes ───────────────────────────────────────────
register_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
