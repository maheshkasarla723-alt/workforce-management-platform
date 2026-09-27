import time
import uuid

from backend.models import Employee


def test_employee_large_dataset_performance(
    client,
    db_session,
):
    """
    PR-033 — realistic large-data benchmark.

    Creates 1,000 employees in the isolated test database,
    then measures the paginated employee-list endpoint.

    This is a benchmark/evidence test, not a production
    performance guarantee.
    """

    # --------------------------------------------------------
    # Create Admin authentication.
    # --------------------------------------------------------

    from tests.test_api import create_test_admin

    headers = {
        "Authorization": (
            f"Bearer {create_test_admin(client, db_session)}"
        )
    }

    # --------------------------------------------------------
    # Create 1,000 employees directly in the test database.
    #
    # Direct inserts keep the benchmark focused on READ
    # performance rather than measuring 1,000 API writes.
    # --------------------------------------------------------

    employees = []

    unique_id = uuid.uuid4().hex[:8]

    for index in range(1000):
        employees.append(
            Employee(
                name=f"Benchmark Employee {index}",
                email=(
                    f"benchmark_{unique_id}_{index}"
                    "@example.com"
                ),
                age=25 + (index % 35),
                salary=30000 + (index * 10),
                status="Active",
                skills="Python, SQL, Excel",
            )
        )

    db_session.bulk_save_objects(employees)
    db_session.commit()

    # --------------------------------------------------------
    # Warm-up request.
    #
    # This prevents the first request from being the only
    # measurement affected by application initialization.
    # --------------------------------------------------------

    warmup = client.get(
        "/api/employees/?page=1&limit=100",
        headers=headers,
    )

    assert warmup.status_code == 200
    assert len(warmup.json()) == 100

    # --------------------------------------------------------
    # Measure three consecutive paginated requests.
    # --------------------------------------------------------

    timings = []

    for page in (1, 5, 10):

        start = time.perf_counter()

        response = client.get(
            f"/api/employees/?page={page}&limit=100",
            headers=headers,
        )

        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        assert len(response.json()) == 100

        timings.append(elapsed)

    # --------------------------------------------------------
    # Calculate statistics.
    # --------------------------------------------------------

    average_time = sum(timings) / len(timings)
    maximum_time = max(timings)

    print()
    print("=" * 60)
    print("PR-033 LARGE-DATA PERFORMANCE BENCHMARK")
    print("=" * 60)
    print("Dataset size : 1,000 employees")
    print("Page size    : 100")
    print(
        "Page timings : "
        + ", ".join(
            f"{value:.4f}s"
            for value in timings
        )
    )
    print(
        f"Average time : {average_time:.4f}s"
    )
    print(
        f"Maximum time : {maximum_time:.4f}s"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Safety threshold for this LOCAL benchmark.
    #
    # This is intentionally generous because this is running
    # through the pytest/FastAPI test environment rather than
    # a production server.
    # --------------------------------------------------------

    assert maximum_time < 2.0, (
        "Large-data employee listing exceeded "
        f"the 2-second local benchmark threshold: "
        f"{maximum_time:.4f}s"
    )
    # ============================================================
# PR-048 — P50 / P95 / P99 LATENCY BASELINE
# ============================================================

def test_employee_api_latency_percentiles(
    client,
    db_session,
):
    """
    PR-048 — Local latency percentile baseline.

    Measures 100 paginated employee-list requests against the
    isolated test application.

    This establishes a reproducible local baseline for:
        p50
        p95
        p99

    This is NOT a production-load measurement.
    """

    import time

    from tests.test_api import create_test_admin

    # --------------------------------------------------------
    # Create Admin authentication.
    # --------------------------------------------------------

    headers = {
        "Authorization": (
            f"Bearer {create_test_admin(client, db_session)}"
        )
    }

    # --------------------------------------------------------
    # Warm-up request.
    # --------------------------------------------------------

    warmup = client.get(
        "/api/employees/?page=1&limit=100",
        headers=headers,
    )

    assert warmup.status_code == 200

    # --------------------------------------------------------
    # Measure 100 requests.
    # --------------------------------------------------------

    timings = []

    for request_number in range(100):

        start = time.perf_counter()

        response = client.get(
            "/api/employees/?page=1&limit=100",
            headers=headers,
        )

        elapsed = time.perf_counter() - start

        assert response.status_code == 200

        timings.append(elapsed)

    # --------------------------------------------------------
    # Sort latency values.
    # --------------------------------------------------------

    timings.sort()

    # --------------------------------------------------------
    # Nearest-rank percentile calculation.
    # --------------------------------------------------------

    def percentile(values, percentile_value):

        rank = int(
            (percentile_value / 100) * len(values)
        )

        rank = max(
            1,
            min(rank, len(values))
        )

        return values[rank - 1]

    p50 = percentile(timings, 50)
    p95 = percentile(timings, 95)
    p99 = percentile(timings, 99)

    average = sum(timings) / len(timings)
    minimum = min(timings)
    maximum = max(timings)

    # --------------------------------------------------------
    # Print performance evidence.
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PR-048 LATENCY PERCENTILE BASELINE")
    print("=" * 60)
    print("Endpoint     : GET /api/employees/")
    print("Requests      : 100")
    print("Page size     : 100")
    print("Environment   : Local isolated test environment")
    print("-" * 60)
    print(f"Minimum       : {minimum:.4f}s")
    print(f"Average       : {average:.4f}s")
    print(f"p50           : {p50:.4f}s")
    print(f"p95           : {p95:.4f}s")
    print(f"p99           : {p99:.4f}s")
    print(f"Maximum       : {maximum:.4f}s")
    print("=" * 60)

    # --------------------------------------------------------
    # Basic sanity check.
    #
    # This test records the baseline rather than claiming
    # production SLA compliance.
    # --------------------------------------------------------

    assert len(timings) == 100
    assert p50 >= 0
    assert p95 >= p50
    assert p99 >= p95

    print("PR-048 latency baseline: RECORDED")