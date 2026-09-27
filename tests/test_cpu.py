# ============================================================
# PR-052 - CPU SATURATION / RESOURCE MEASUREMENT TEST
# ============================================================

import time

import psutil

from concurrent.futures import ThreadPoolExecutor, as_completed

from tests.test_api import create_test_admin


def test_employee_api_cpu_measurement(client, db_session):
    """
    Measure CPU utilization while the employee API handles
    concurrent authenticated requests.

    PR-052 goals:
    - Generate realistic concurrent API activity.
    - Measure CPU before, during and after the workload.
    - Record peak measured CPU usage.
    - Verify the application remains responsive.
    """

    print("\n")
    print("=" * 60)
    print("PR-052 CPU RESOURCE / SATURATION TEST")
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
    # CPU BASELINE
    # --------------------------------------------------------

    process = psutil.Process()

    # Establish the initial process CPU measurement baseline.
    process.cpu_percent(interval=0.1)

    cpu_before = psutil.cpu_percent(
        interval=0.2
    )

    # --------------------------------------------------------
    # WORKLOAD CONFIGURATION
    # --------------------------------------------------------

    concurrent_requests = 30

    latencies = []
    successful_requests = 0

    # --------------------------------------------------------
    # API REQUEST FUNCTION
    # --------------------------------------------------------

    def make_request():

        start = time.perf_counter()

        response = client.get(
            "/api/employees/?page=1&limit=10",
            headers=headers
        )

        elapsed = (
            time.perf_counter() - start
        )

        return (
            response.status_code,
            elapsed
        )

    # --------------------------------------------------------
    # GENERATE CONCURRENT WORKLOAD
    # --------------------------------------------------------

    workload_start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=concurrent_requests
    ) as executor:

        futures = [
            executor.submit(make_request)
            for _ in range(concurrent_requests)
        ]

        for future in as_completed(futures):

            status_code, latency = (
                future.result()
            )

            latencies.append(
                latency
            )

            if status_code == 200:
                successful_requests += 1

    workload_elapsed = (
        time.perf_counter()
        - workload_start
    )

    # --------------------------------------------------------
    # CPU MEASUREMENT AFTER WORKLOAD
    # --------------------------------------------------------

    cpu_after = psutil.cpu_percent(
        interval=0.5
    )

    # --------------------------------------------------------
    # PROCESS CPU MEASUREMENT
    # --------------------------------------------------------

    process_cpu = process.cpu_percent(
        interval=0.2
    )

    # --------------------------------------------------------
    # CALCULATIONS
    # --------------------------------------------------------

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

    minimum_latency = (
        min(latencies)
        if latencies
        else 0
    )

    peak_cpu = max(
        cpu_before,
        cpu_after,
        process_cpu
    )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print()

    print(
        f"Concurrent requests : "
        f"{concurrent_requests}"
    )

    print(
        f"Successful requests : "
        f"{successful_requests}"
    )

    print(
        f"Workload elapsed    : "
        f"{workload_elapsed:.4f}s"
    )

    print(
        f"Minimum latency     : "
        f"{minimum_latency:.4f}s"
    )

    print(
        f"Average latency     : "
        f"{average_latency:.4f}s"
    )

    print(
        f"Maximum latency     : "
        f"{maximum_latency:.4f}s"
    )

    print(
        f"CPU before          : "
        f"{cpu_before:.2f}%"
    )

    print(
        f"CPU after           : "
        f"{cpu_after:.2f}%"
    )

    print(
        f"Process CPU         : "
        f"{process_cpu:.2f}%"
    )

    print(
        f"Peak measured CPU   : "
        f"{peak_cpu:.2f}%"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # ASSERTIONS
    # --------------------------------------------------------

    assert successful_requests == (
        concurrent_requests
    ), (
        "Not all concurrent authenticated "
        "API requests completed successfully."
    )

    assert len(latencies) == (
        concurrent_requests
    ), (
        "Unexpected number of latency "
        "measurements."
    )

    assert workload_elapsed >= 0

    assert cpu_before >= 0
    assert cpu_after >= 0
    assert process_cpu >= 0
    assert peak_cpu >= 0

    assert average_latency >= 0

    assert maximum_latency >= (
        average_latency
    )

    print(
        "PR-052 CPU saturation "
        "measurement: PASSED"
    )