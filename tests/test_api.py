from fastapi.testclient import TestClient
from icoapi.fastapi_app import app
c = TestClient(app)
def test_root(): assert c.get("/").status_code == 200
