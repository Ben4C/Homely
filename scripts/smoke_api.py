"""Run with API already started: python scripts/smoke_api.py"""
import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000/api/v1"
PATHS = ["/health", "/programs", "/applications", "/donors/campaigns", "/employers/programs", "/projects", "/admin/review-queue"]


# Purpose: Smoke test all role-list endpoints against a running local FastAPI instance.
# Inputs: BASE_URL constant, no user secrets or live data.
# Outputs: Prints endpoint status and demo flag; exits with exception on request failure.
def main() -> None:
    for path in PATHS:
        with urllib.request.urlopen(BASE_URL + path, timeout=4) as response:
            obj = json.load(response)
        print(path, "OK", "demo=" + str(obj.get("demo", "n/a")))


if __name__ == "__main__":
    main()
