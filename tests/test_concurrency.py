# ============================================================
# PR-049 — CONCURRENT USER / REQUEST TEST
# ============================================================

from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from tests.test_api import create_test_admin


def test_employee_api_concurrent_requests(
    client,
    db_session,
):
    """
    PR-049 — Concurrent request baseline.

    Sends 20 simultaneous GET requests to the employee-list
    endpoint and verifies that all requests succeed.

    This is a local isolated-test benchmark and is NOT a
    production load test.
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
    # Define one concurrent request.
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
    # Run 20 requests concurrently.
    # --------------------------------------------------------

    results = []

    start_all = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=20
    ) as executor:

        futures = [
            executor.submit(
                make_request,
                request_number,
            )
            for request_number in range(1, 21)
        ]

        for future in as_completed(futures):
            results.append(
                future.result()
            )

    total_elapsed = (
        time.perf_counter() - start_all
    )

    # --------------------------------------------------------
    # Sort results by request number.
    # --------------------------------------------------------

    results.sort(
        key=lambda item: item["request"]
    )

    # --------------------------------------------------------
    # Validate every request.
    # --------------------------------------------------------

    assert len(results) == 20

    failed_requests = [
        result
        for result in results
        if result["status_code"] != 200
    ]

    assert not failed_requests, (
        "Concurrent requests failed: "
        f"{failed_requests}"
    )

    # --------------------------------------------------------
    # Calculate latency statistics.
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
    # Print evidence.
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PR-049 CONCURRENT REQUEST TEST")
    print("=" * 60)
    print("Concurrent requests : 20")
    print("Successful requests : "
          f"{successful_requests}")
    print(
        f"Total elapsed       : "
        f"{total_elapsed:.4f}s"
    )
    print(
        f"Average latency     : "
        f"{average_latency:.4f}s"
    )
    print(
        f"Maximum latency     : "
        f"{maximum_latency:.4f}s"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Basic safety assertions.
    # --------------------------------------------------------

    assert successful_requests == 20
    assert average_latency >= 0
    assert maximum_latency >= average_latency

    print(
        "PR-049 concurrent request test: PASSED"
    )