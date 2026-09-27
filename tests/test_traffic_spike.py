# ============================================================
# PR-050 — TRAFFIC SPIKE TEST
# ============================================================

from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from tests.test_api import create_test_admin


def test_employee_api_traffic_spike(
    client,
    db_session,
):
    """
    PR-050 — Controlled traffic-spike test.

    Sends a short burst of 50 requests using 25 concurrent
    workers, verifies that the API remains successful, and
    then verifies that the API responds normally after the
    burst.

    This is a local isolated-test benchmark and is NOT a
    production capacity test.
    """

    # --------------------------------------------------------
    # Create authentication.
    # --------------------------------------------------------

    token = create_test_admin(
        client,
        db_session,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # --------------------------------------------------------
    # Traffic-spike configuration.
    # --------------------------------------------------------

    total_requests = 50
    concurrent_workers = 25

    # --------------------------------------------------------
    # One request.
    # --------------------------------------------------------

    def make_request(request_number):

        start = time.perf_counter()

        response = client.get(
            "/api/employees/?page=1&limit=100",
            headers=headers,
        )

        elapsed = (
            time.perf_counter() - start
        )

        return {
            "request": request_number,
            "status_code": response.status_code,
            "elapsed": elapsed,
        }

    # --------------------------------------------------------
    # Execute traffic spike.
    # --------------------------------------------------------

    results = []

    spike_start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=concurrent_workers
    ) as executor:

        futures = [
            executor.submit(
                make_request,
                request_number,
            )
            for request_number in range(
                1,
                total_requests + 1,
            )
        ]

        for future in as_completed(futures):
            results.append(
                future.result()
            )

    spike_elapsed = (
        time.perf_counter() - spike_start
    )

    # --------------------------------------------------------
    # Sort results.
    # --------------------------------------------------------

    results.sort(
        key=lambda item: item["request"]
    )

    # --------------------------------------------------------
    # Validate request count.
    # --------------------------------------------------------

    assert len(results) == total_requests

    # --------------------------------------------------------
    # Identify failures.
    # --------------------------------------------------------

    failed_requests = [
        result
        for result in results
        if result["status_code"] != 200
    ]

    server_errors = [
        result
        for result in results
        if 500 <= result["status_code"] <= 599
    ]

    # --------------------------------------------------------
    # Traffic-spike assertions.
    # --------------------------------------------------------

    assert not failed_requests, (
        "Traffic spike produced failed requests: "
        f"{failed_requests}"
    )

    assert not server_errors, (
        "Traffic spike produced server errors: "
        f"{server_errors}"
    )

    # --------------------------------------------------------
    # Calculate latency.
    # --------------------------------------------------------

    latencies = [
        result["elapsed"]
        for result in results
    ]

    average_latency = (
        sum(latencies) / len(latencies)
    )

    maximum_latency = max(latencies)

    successful_requests = sum(
        1
        for result in results
        if result["status_code"] == 200
    )

    # --------------------------------------------------------
    # Recovery check after traffic spike.
    # --------------------------------------------------------

    recovery_start = time.perf_counter()

    recovery_response = client.get(
        "/api/employees/?page=1&limit=10",
        headers=headers,
    )

    recovery_elapsed = (
        time.perf_counter() - recovery_start
    )

    assert recovery_response.status_code == 200

    # --------------------------------------------------------
    # Evidence output.
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PR-050 TRAFFIC SPIKE TEST")
    print("=" * 60)
    print(
        f"Traffic spike requests : "
        f"{total_requests}"
    )
    print(
        f"Concurrent workers     : "
        f"{concurrent_workers}"
    )
    print(
        f"Successful requests    : "
        f"{successful_requests}"
    )
    print(
        f"Spike elapsed          : "
        f"{spike_elapsed:.4f}s"
    )
    print(
        f"Average latency        : "
        f"{average_latency:.4f}s"
    )
    print(
        f"Maximum latency        : "
        f"{maximum_latency:.4f}s"
    )
    print(
        f"Recovery status        : "
        f"{recovery_response.status_code}"
    )
    print(
        f"Recovery latency       : "
        f"{recovery_elapsed:.4f}s"
    )
    print("=" * 60)

    print(
        "PR-050 traffic spike test: PASSED"
    )