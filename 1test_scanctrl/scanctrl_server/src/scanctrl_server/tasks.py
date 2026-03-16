import logging
import threading
import time

log = logging.getLogger(__name__)

class BackgroundTask:
    def __init__(self):
        self._running = False
        self._thread = None

    def _task_loop(self):
        while self._running:
            log.info("Background task running...")
            time.sleep(5)

    def start(self):
        if self._running:
            return "Task already running."
        self._running = True
        self._thread = threading.Thread(target=self._task_loop, daemon=True)
        self._thread.start()
        return "Task started."

    def stop(self):
        if not self._running:
            return "Task not running."
        self._running = False
        self._thread.join()
        return "Task stopped."

    def status(self):
        return "running" if self._running else "stopped"

bg_task = BackgroundTask()