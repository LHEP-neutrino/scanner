import requests
from myproject.config import Config

# ----------------------------------------------------------------------
# Define teh Client class that will deal with the http requests
# ----------------------------------------------------------------------

class Client:
    def __init__(self):
        cfg = Config().parse_yaml()
        self.api_key = cfg.get("API_KEY")
        self.host = cfg.get("AppHost", "127.0.0.1")
        self.port = cfg.get("AppPort", 5000)
        self.base_url = f"http://{self.host}:{self.port}"

    def status(self):
        """Return the server status."""
        try:
            resp = requests.get(f"{self.base_url}/status")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def debug(self, data=None):
        """Send debug command to server."""
        data = data or {}
        try:
            resp = requests.post(f"{self.base_url}/debug", json=data)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
        
    def process_files(self, path: str):
        """
        Ask the server to start the file processing task.
        """
        try:
            resp = requests.post(
                f"{self.base_url}/process-files",
                json={"path": path},
                timeout=5,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
