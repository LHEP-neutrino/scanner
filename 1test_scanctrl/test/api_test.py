
import sys
sys.path.append(str("/Users/nsallin/develop/scanner/scanner/scanctrl/scanctrl_server"))

from src.scanctrl_server.api import app

client = app.test_client()
resp = client.get("/status")
print(resp)
assert resp.status_code == 200