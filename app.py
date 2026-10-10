"""RepoBuddy AI - Flask backend."""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from ai_service import AIConfigError, AIResponseError, analyze_issue

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "model_id": os.environ.get("MODEL_ID", "llama3.2:3b")})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("issue"), str):
        return jsonify({"error": "Please send the issue text."}), 400

    issue_text = data["issue"].strip()
    if len(issue_text) < 15:
        return jsonify({"error": "That issue looks too short. Paste the full text."}), 400
    if len(issue_text) > 12000:
        return jsonify({"error": "That issue is too long. Trim it under 12000 characters."}), 400

    try:
        return jsonify(analyze_issue(issue_text)), 200
    except AIConfigError as exc:
        return jsonify({"error": str(exc)}), 503
    except AIResponseError as exc:
        return jsonify({"error": str(exc)}), 502
    except Exception as exc:
        return jsonify({"error": f"Unexpected error: {exc}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
    
