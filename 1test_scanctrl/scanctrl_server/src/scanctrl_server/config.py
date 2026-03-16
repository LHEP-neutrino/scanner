# Server configuration
import os

API_HOST = os.getenv("SCANCTRL_HOST", "127.0.0.1")
API_PORT = int(os.getenv("SCANCTRL_PORT", "5000"))
API_KEY  = os.getenv("SCANCTRL_API_KEY", "secretKey")
LOG_LEVEL = "INFO"