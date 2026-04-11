"""
routes.py — Flask route definitions
  GET  /            → serves the main UI
  POST /check       → full analysis (on-demand)
  POST /realtime    → lightweight analysis for debounced typing
"""

from flask import jsonify, render_template, request
from quality_checker import analyze


def register_routes(app):

    # ── Main UI ───────────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        return render_template("index.html")

    # ── Full Analysis ─────────────────────────────────────────────────────────
    @app.route("/check", methods=["POST"])
    def check():
        """
        Accepts: { "text": "..." }
        Returns: full analysis JSON (see quality_checker.analyze)
        """
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"error": "No text provided."}), 400

        result = analyze(text)
        return jsonify(result)

    # ── Real-Time (debounced) ─────────────────────────────────────────────────
    @app.route("/realtime", methods=["POST"])
    def realtime():
        """
        Same as /check but intended for frequent calls while typing.
        Returns only the fields needed to update the live suggestion UI.
        """
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()

        if not text:
            return jsonify({
                "improved": "",
                "score": {"total": 0, "label": "Poor"},
                "has_empathy": False,
                "tone": "Neutral",
                "error_count": 0,
            })

        result = analyze(text)
        return jsonify({
            "improved": result["improved"],
            "corrected": result["corrected"],
            "score": result["score"],
            "has_empathy": result["empathy"]["has_empathy"],
            "empathy_suggestion": result["empathy"]["suggestion"],
            "tone": result["tone"],
            "error_count": len(result["grammar_errors"]),
            "grammar_errors": result["grammar_errors"],
        })
