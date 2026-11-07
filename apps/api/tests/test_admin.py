from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)


# Purpose: Verify admin queue is explicitly synthetic for the demo.
# Inputs: Empty GET.
# Outputs: Test confirms demo flag, no live private cases.
def test_admin_queue_is_demo() -> None:
    response = client.get("/api/v1/admin/review-queue")
    assert response.status_code == 200
    assert response.json()["demo"] is True
