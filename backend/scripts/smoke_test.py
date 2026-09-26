import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"

SCENARIOS = {
    "safe": "SAFE",
    "caution": "CAUTION",
    "unsafe": "UNSAFE",
    "blocked": "BLOCKED",
    "data_unavailable": "DATA_UNAVAILABLE",
}


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    print("\nORCA LOCAL SMOKE TEST")
    print("=" * 50)

    # 1. Health
    response = httpx.get(
        f"{BASE_URL}/health",
        timeout=10
    )

    check(
        response.status_code == 200,
        f"/health returned {response.status_code}"
    )

    print("PASS  /health")

    # 2. Demo scenarios
    for scenario, expected_status in SCENARIOS.items():

        response = httpx.get(
            f"{BASE_URL}/api/demo",
            params={
                "scenario": scenario,
                "location": "Kakinada",
            },
            timeout=10,
        )

        check(
            response.status_code == 200,
            f"{scenario}: HTTP {response.status_code}"
        )

        data = response.json()

        # Risk
        actual_status = data["risk"]["status"]

        check(
            actual_status == expected_status,
            f"{scenario}: expected {expected_status}, got {actual_status}"
        )

        # Trace
        trace = data.get("trace", [])

        check(
            len(trace) == 6,
            f"{scenario}: expected 6 trace stages, got {len(trace)}"
        )

        check(
            trace[0]["stage"] == "Intent",
            f"{scenario}: first stage is not Intent"
        )

        check(
            trace[-1]["stage"] == "Explanation",
            f"{scenario}: last stage is not Explanation"
        )

        # Route
        route_safe = data.get(
            "route", {}
        ).get("safe_to_navigate")

        expected_route_safe = scenario in {
            "safe",
            "caution"
        }

        check(
            route_safe == expected_route_safe,
            f"{scenario}: route safety mismatch"
        )

        print(
            f"PASS  {scenario:<17} "
            f"risk={actual_status:<16} "
            f"trace=6 "
            f"route_safe={route_safe}"
        )

    print("=" * 50)
    print("ALL ORCA LOCAL TESTS PASSED")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\nSMOKE TEST FAILED")
        print(f"ERROR: {error}")
        sys.exit(1)