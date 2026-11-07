from fastapi.testclient import TestClient
from app.main import app


# Purpose: Validate API boot and demo-mode signal.
# Inputs: Empty GET to /api/v1/health.
# Outputs: HTTP 200, status ok and demo true.
def test_health() -> None:
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"service":"homely-api","status":"ok","demo":True}
