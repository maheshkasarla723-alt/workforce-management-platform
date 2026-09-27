# ============================================================
# PR-053 - MEMORY GROWTH / RESOURCE MEASUREMENT TEST
# ============================================================

import gc
import time

import psutil

from tests.test_api import create_test_admin


def test_employee_api_memory_growth(client, db_session):
    """
    Measure process memory before and after repeated authenticated
    employee API requests.

    PR-053 goals:
    - Establish a process memory baseline.
    - Generate repeated API activity.
    - Measure memory after the workload.
    - Calculate memory growth.
    - Verify all API requests remain successful.
    - Detect excessive memory growth during the test workload.
    """

    print("\n")
    print("=" * 60)
    print("PR-053 MEMORY GROWTH / RESOURCE TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # CREATE AUTHENTICATED ADMIN TOKEN
    # --------------------------------------------------------

    token = create_test_admin(
        client,
        db_session
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # --------------------------------------------------------
    # PROCESS INFORMATION
    # --------------------------------------------------------

    process = psutil.Process()

    # Clean up temporary Python objects before baseline.
    gc.collect()

    # Give the process a moment to settle.
    time.sleep(0.1)

    memory_before = process.memory_info().rss

    # --------------------------------------------------------
    # WORKLOAD CONFIGURATION
    # --------------------------------------------------------

    total_requests = 300

    successful_requests = 0
    latencies = []

    # --------------------------------------------------------
    # GENERATE REPEATED API WORKLOAD
    # --------------------------------------------------------

    workload_start = time.perf_counter()

    for _ in range(total_requests):

        start = time.perf_counter()

        response = client.get(
            "/api/employees/?page=1&limit=10",
            headers=headers
        )

        elapsed = (
            time.perf_counter() - start
        )

        latencies.append(elapsed)

        if response.status_code == 200:
            successful_requests += 1

    workload_elapsed = (
        time.perf_counter()
        - workload_start
    )

    # --------------------------------------------------------
    # CLEAN UP BEFORE FINAL MEMORY MEASUREMENT
    # --------------------------------------------------------

    gc.collect()

    time.sleep(0.1)

    memory_after = process.memory_info().rss

    # --------------------------------------------------------
    # MEMORY CALCULATIONS
    # --------------------------------------------------------

    memory_before_mb = (
        memory_before / (1024 * 1024)
    )

    memory_after_mb = (
        memory_after / (1024 * 1024)
    )

    memory_growth_mb = (
        memory_after_mb
        - memory_before_mb
    )

    average_latency = (
        sum(latencies) / len(latencies)
        if latencies
        else 0
    )

    maximum_latency = (
        max(latencies)
        if latencies
        else 0
    )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print()

    print(
        f"Requests             : "
        f"{total_requests}"
    )

    print(
        f"Successful requests  : "
        f"{successful_requests}"
    )

    print(
        f"Workload elapsed     : "
        f"{workload_elapsed:.4f}s"
    )

    print(
        f"Memory before        : "
        f"{memory_before_mb:.2f} MB"
    )

    print(
        f"Memory after         : "
        f"{memory_after_mb:.2f} MB"
    )

    print(
        f"Memory growth        : "
        f"{memory_growth_mb:.2f} MB"
    )

    print(
        f"Average latency      : "
        f"{average_latency:.4f}s"
    )

    print(
        f"Maximum latency      : "
        f"{maximum_latency:.4f}s"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # ASSERTIONS
    # --------------------------------------------------------

    assert successful_requests == (
        total_requests
    ), (
        "Not all repeated authenticated "
        "API requests completed successfully."
    )

    assert len(latencies) == (
        total_requests
    ), (
        "Unexpected number of latency "
        "measurements."
    )

    assert memory_before_mb > 0

    assert memory_after_mb > 0

    assert memory_growth_mb >= 0 or memory_growth_mb < 0

    assert workload_elapsed >= 0

    assert average_latency >= 0

    assert maximum_latency >= (
        average_latency
    )

    # --------------------------------------------------------
    # MEMORY GROWTH THRESHOLD
    #
    # This is a local benchmark threshold for the
    # 300-request test workload, not a production
    # infrastructure memory limit.
    # --------------------------------------------------------

    assert memory_growth_mb < 50, (
        "Excessive process memory growth detected: "
        f"{memory_growth_mb:.2f} MB after "
        f"{total_requests} requests."
    )

    print(
        "PR-053 memory growth "
        "measurement: PASSED"
    )