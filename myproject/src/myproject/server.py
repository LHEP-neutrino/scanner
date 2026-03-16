import logging
from systemd.journal import JournalHandler
from flask import Flask, request, jsonify
from waitress import serve
from myproject.config import Config
from myproject.task_manager import TaskManager

# ----------------------------------------------------------------------
# Logging setup (journald + console)
# ----------------------------------------------------------------------

# Logging
logger = logging.getLogger("myproject-server")
logger.setLevel(logging.INFO)

# Journald handler (systemd)
journald_handler = JournalHandler()
journald_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
logger.addHandler(journald_handler)

# Console handler (useful when not running under systemd)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
logger.addHandler(console_handler)

# ----------------------------------------------------------------------
# Flask app and task manager
# ----------------------------------------------------------------------

app = Flask(__name__)

# Single TaskManager instance for the whole process
task_manager = TaskManager()

# ----------------------------------------------------------------------
# Request logging (lightweight, safe)
# ----------------------------------------------------------------------

@app.before_request
def log_request_info():
    logger.info(f"Received {request.method} request for {request.url}")
    if request.method == 'POST':
        logger.info(f"Request data: {request.get_json()}")

# ----------------------------------------------------------------------
# Task implementations
# ----------------------------------------------------------------------        

def debug_task(message: str):
    """
    Example background task.
    This runs outside the Flask request thread.
    """
    logger.info("Debug task started", extra={"message": message})
    logger.info("hello")  # this will appear in journald
    logger.info("Debug task finished")

def process_files_task(path: str):
    logger.info("Processing files", extra={"path": path})
    # long-running work here

# ----------------------------------------------------------------------
# API endpoints
# ----------------------------------------------------------------------

@app.route("/status", methods=["GET"])
def status():
    """
    Return server status and current running task.
    """
    return jsonify({
        "status": "running",
        "current_task": task_manager.status(),
    })



@app.route("/debug", methods=["POST"])
def debug():
    """
    Start the debug task.
    """
    data = request.get_json(silent=True) or {}
    message = data.get("message", "hello")

    ok, msg = task_manager.start_task(
        name="debug",
        target=debug_task,
        message=message,
    )

    return jsonify({"message": msg}), 200 if ok else 409



@app.route("/process-files", methods=["POST"])
def process_files():
    data = request.get_json() or {}
    path = data.get("path")

    if not path:
        return jsonify({"error": "path is required"}), 400

    ok, msg = task_manager.start_task(
        name="process_files",
        target=process_files_task,
        path=path
    )

    return jsonify({"message": msg}), 200 if ok else 409

# ----------------------------------------------------------------------
# Server startup
# ----------------------------------------------------------------------

def start_app():
    """
    Start the Waitress server using configuration.
    """
    cfg = Config().parse_yaml()
    host = cfg.get("AppHost", "0.0.0.0")
    port = cfg.get("AppPort", 5000)

    logger.info(
        "Starting MyProject server",
        extra={"host": host, "port": port},
    )

    serve(app, host=host, port=port, _quiet=False)

if __name__ == "__main__":
    start_app()
