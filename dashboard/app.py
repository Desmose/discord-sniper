import json
import time
from pathlib import Path

from flask import Flask, jsonify, render_template

STATUS_DIR = Path("/app/status")

app = Flask(__name__)


def read_all_status():
    accounts = []
    if STATUS_DIR.exists():
        for f in sorted(STATUS_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                data["age_seconds"] = max(0, time.time() - _parse_iso(data.get("last_update")))
                accounts.append(data)
            except (json.JSONDecodeError, OSError):
                continue
    accounts.sort(key=lambda a: a.get("account", ""))
    return accounts


def _parse_iso(s):
    if not s:
        return time.time()
    try:
        from datetime import datetime
        return datetime.fromisoformat(s).timestamp()
    except ValueError:
        return time.time()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    accounts = read_all_status()
    totals = {
        "attempts": sum(a.get("attempts_total", 0) for a in accounts),
        "remaining": sum(a.get("remaining", 0) for a in accounts),
        "total_candidates": sum(a.get("total_candidates", 0) for a in accounts),
        "found": [name for a in accounts for name in a.get("found", [])],
        "accounts_online": len(accounts),
    }
    return jsonify({"accounts": accounts, "totals": totals})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
