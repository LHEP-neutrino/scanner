from flask import Flask, jsonify, request
from .config import API_KEY

app = Flask(__name__)

@app.route("/status")
def status():
    return jsonify({"status": "running"})

@app.route("/secure", methods=["POST"])
def secure():
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"message": "secure data"})
