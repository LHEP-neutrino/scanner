# src/myproject/task_manager.py
import threading
import logging

logger = logging.getLogger("myproject-server")

class TaskManager:
    def __init__(self):
        self._current_task = None
        self._task_lock = threading.Lock()
        self._process_lock = threading.Lock()

    def start_task(self, name, target, *args, **kwargs):
        with self._task_lock:
            if self._current_task is not None:
                return False, "Another task is already running"

            thread = threading.Thread(
                target=self._run_task,
                args=(name, target, *args),
                kwargs=kwargs,
                daemon=True,
            )

            self._current_task = name
            thread.start()

            logger.info("Task started", extra={"task": name})
            return True, f"Task '{name}' started"

    def _run_task(self, name, target, *args, **kwargs):
        try:
            with self._process_lock:
                target(*args, **kwargs)
        except Exception:
            logger.exception("Task failed", extra={"task": name})
        finally:
            with self._task_lock:
                logger.info("Task finished", extra={"task": name})
                self._current_task = None

    def status(self):
        with self._task_lock:
            return self._current_task or "idle"
