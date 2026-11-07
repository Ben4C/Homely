from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    status: str
    demo: bool


# Purpose: Return a typed status payload for operational smoke tests.
# Inputs: None.
# Outputs: HealthResponse with explicit demo indicator.
def get_health() -> HealthResponse:
    return HealthResponse(service="homely-api", status="ok", demo=True)
