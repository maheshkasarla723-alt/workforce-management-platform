# ============================================================
# PR-051 — SUSTAINED WORKLOAD / SOAK TEST
# ============================================================

import time

from tests.test_api import create_test_admin


def test_employee_api_sustained_workload(
    client,
    db_session,
):
    """
    PR-051 — Controlled sustained-workload test.

    Executes 300 consecutive employee-list requests with a
    short interval between requests.

    This verifies that the API remains available and successful
    throughout the sustained workload.

    This is a local isolated-test benchmark and is NOT a
    production-duration soak test.
    """

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    token = create_test_admin(
        client,
        db_session,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # --------------------------------------------------------
    # Workload configuration
    # --------------------------------------------------------

    total_requests = 300
    interval_seconds = 0.02

    results = []

    # --------------------------------------------------------
    # Execute sustained workload
    # --------------------------------------------------------

    workload_start = time.perf_counter()

    for request_number in range(
        1,
        total_requests + 1,
    ):

        request_start = time.perf_counter()

        response = client.get(
            "/api/employees/?page=1&limit=100",
            headers=headers,
        )

        elapsed = (
            time.perf_counter() - request_start
        )

        results.append(
            {
                "request": request_number,
                "status_code": response.status_code,
                "elapsed": elapsed,
            }
        )

        # Small controlled interval between requests.
        time.sleep(interval_seconds)

    workload_elapsed = (
        time.perf_counter() - workload_start
    )

    # --------------------------------------------------------
    # Validate request count
    # --------------------------------------------------------

    assert len(results) == total_requests

    # --------------------------------------------------------
    # Find failed requests
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
    # Reliability assertions
    # --------------------------------------------------------

    assert not failed_requests, (
        "Sustained workload produced failed requests: "
        f"{failed_requests[:10]}"
    )

    assert not server_errors, (
        "Sustained workload produced server errors: "
        f"{server_errors[:10]}"
    )

    # --------------------------------------------------------
    # Latency statistics
    # --------------------------------------------------------

    latencies = [
        result["elapsed"]
        for result in results
    ]

    average_latency = (
        sum(latencies) / len(latencies)
    )

    minimum_latency = min(latencies)
    maximum_latency = max(latencies)

    # --------------------------------------------------------
    # Compare first and final workload batches
    # --------------------------------------------------------

    batch_size = 30

    first_batch = latencies[:batch_size]
    final_batch = latencies[-batch_size:]

    first_batch_average = (
        sum(first_batch) / len(first_batch)
    )

    final_batch_average = (
        sum(final_batch) / len(final_batch)
    )

    successful_requests = sum(
        1
        for result in results
        if result["status_code"] == 200
    )

    # --------------------------------------------------------
    # Final recovery request
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
    # Evidence output
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PR-051 SUSTAINED WORKLOAD / SOAK TEST")
    print("=" * 60)
    print(
        f"Requests              : "
        f"{total_requests}"
    )
    print(
        f"Interval              : "
        f"{interval_seconds:.3f}s"
    )
    print(
        f"Successful requests   : "
        f"{successful_requests}"
    )
    print(
        f"Total workload time   : "
        f"{workload_elapsed:.4f}s"
    )
    print(
        f"Minimum latency       : "
        f"{minimum_latency:.4f}s"
    )
    print(
        f"Average latency       : "
        f"{average_latency:.4f}s"
    )
    print(
        f"Maximum latency       : "
        f"{maximum_latency:.4f}s"
    )
    print(
        f"First 30 avg latency  : "
        f"{first_batch_average:.4f}s"
    )
    print(
        f"Final 30 avg latency  : "
        f"{final_batch_average:.4f}s"
    )
    print(
        f"Recovery status       : "
        f"{recovery_response.status_code}"
    )
    print(
        f"Recovery latency      : "
        f"{recovery_elapsed:.4f}s"
    )
    print("=" * 60)

    print(
        "PR-051 sustained workload test: PASSED"
    )