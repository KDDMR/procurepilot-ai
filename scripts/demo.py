import json
import sys

import httpx

BASE_URL = "http://127.0.0.1:8000"

payload = {
    "requester": "Kadir Demir",
    "department": "Research & Development",
    "vendor": "Fabrikam Analytics Ltd",
    "amount_eur": 128_000,
    "description": "Cloud quality inspection service processing production images.",
    "data_classification": "restricted",
    "contains_personal_data": True,
    "single_source": True,
    "urgent": True,
}

try:
    response = httpx.post(f"{BASE_URL}/api/v1/assessments", json=payload, timeout=20)
    response.raise_for_status()
except httpx.HTTPError as error:
    print(f"Demo failed: {error}. Is the API running on {BASE_URL}?", file=sys.stderr)
    raise SystemExit(1) from error

print(json.dumps(response.json(), indent=2))
