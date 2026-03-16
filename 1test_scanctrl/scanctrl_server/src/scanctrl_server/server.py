import logging
import signal
import sys
from threading import Thread
from werkzeug.serving import make_server
from .api import create_app
from . import config

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
log = logging.getLogger(__name__)

class FlaskServer:
    def __init__(self, host=config.HOST, port=config.PORT):
        self.host = host
        self.port = port
        self.app = create_app()
        self._server = make_server(host, port, self.app)
        self._thread = Thread(target=self._server.serve_forever)
    
    def start(self):
        log.info(f"Starting Flask server on {self.host}:{self.port}")
        self._thread.start()
    
    def stop(self):
        log.info("Stopping Flask server...")
        self._server.shutdown()
        self._thread.join()
        log.info("Flask server stopped")

if __name__ == "__main__":
    server = FlaskServer()
    
    def handle_sigterm(signum, frame):
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)
    server.start()
    
    try:
        signal.pause()
    except KeyboardInterrupt:
        server.stop()
