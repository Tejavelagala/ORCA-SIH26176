"""Local ORCA smoke test for the deterministic demo API.

Run with the FastAPI server already started:
    python backend/scripts/smoke_test.py

This script intentionally does not depend on GitHub Actions or external providers.
"""

import json
import sys
from urllib.request import urlopen

BASE_URL = "http://127.0.0.1:8000"
SCENARIOS = {
    "safe": "SAFE",
    "caution": "CAUTION",
    "unsafe": "UNSAFE",
    "blocked": "BLOCKED",
    "data_unavailable": "DATA_UNAVAILABLE",
}


def get_json(path: str) -> dict:
    with urlopen(BASE_URL + path, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    print("ORCA local smoke test")
    print("=" * 24)

    health = get_json("/health")
    assert health == {"status": "healthy"}
    print("[PASS] /health")

    for scenario, expected_status in SCENARIOS.items():
        payload = get_json(f"/api/demo?scenario={scenario}&location=Kakinada")
        actual_status = payload["risk"]["status"]
        assert actual_status == expected_status, (
            f"{scenario}: expected {expected_status}, got {actual_status}"
        )
        assert len(payload["trace"]) == 6
        assert payload["trace"][0]["stage"] == "Intent"
        assert payload["trace"][-1]["stage"] == "Explanation"

        route_safe = payload["route"]["safe_to_navigate"]
        expected_route_safe = expected_status in {"SAFE", "CAUTION"}
        assert route_safe is expected_route_safe

        print(f"[PASS] {scenario:16} -> {actual_status}")

    print("=" * 24)
    print("All local deterministic demo checks passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)
