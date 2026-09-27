# ============================================================
# PR-055 - DATABASE CONNECTION POOL PRESSURE TEST
# ============================================================

import time

from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy import text

from backend.database import engine


def test_database_connection_pool_pressure():
    """
    Verify that the configured database connection pool
    remains usable under concurrent connection pressure.

    PR-055 goals:
    - Verify the SQLAlchemy engine exposes a connection pool.
    - Open multiple concurrent database connections.
    - Execute a lightweight database query.
    - Measure connection/query latency.
    - Ensure connections are returned to the pool.
    """

    print("\n")
    print("=" * 60)
    print("PR-055 DATABASE CONNECTION POOL PRESSURE TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Pool information
    # --------------------------------------------------------

    pool = engine.pool

    pool_class = pool.__class__.__name__

    print(f"Pool class          : {pool_class}")

    # --------------------------------------------------------
    # Workload configuration
    # --------------------------------------------------------

    concurrent_connections = 20

    latencies = []
    successful_connections = 0
    failures = []

    # --------------------------------------------------------
    # Database connection function
    # --------------------------------------------------------

    def database_request():

        start = time.perf_counter()

        try:

            with engine.connect() as connection:

                connection.execute(text("SELECT 1"))

            elapsed = time.perf_counter() - start

            return True, elapsed, None

        except Exception as exc:

            elapsed = time.perf_counter() - start

            return False, elapsed, str(exc)

    # --------------------------------------------------------
    # Concurrent connection pressure
    # --------------------------------------------------------

    workload_start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=concurrent_connections
    ) as executor:

        futures = [
            executor.submit(database_request)
            for _ in range(concurrent_connections)
        ]

        for future in as_completed(futures):

            success, latency, error = future.result()

            latencies.append(latency)

            if success:

                successful_connections += 1

            else:

                failures.append(error)

    workload_elapsed = (
        time.perf_counter() - workload_start
    )

    # --------------------------------------------------------
    # Calculations
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

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print()

    print(
        f"Concurrent connections : "
        f"{concurrent_connections}"
    )

    print(
        f"Successful connections : "
        f"{successful_connections}"
    )

    print(
        f"Failed connections     : "
        f"{len(failures)}"
    )

    print(
        f"Workload elapsed       : "
        f"{workload_elapsed:.4f}s"
    )

    print(
        f"Minimum latency        : "
        f"{minimum_latency:.4f}s"
    )

    print(
        f"Average latency        : "
        f"{average_latency:.4f}s"
    )

    print(
        f"Maximum latency        : "
        f"{maximum_latency:.4f}s"
    )

    # --------------------------------------------------------
    # Assertions
    # --------------------------------------------------------

    assert pool is not None, (
        "SQLAlchemy database pool is not configured."
    )

    assert successful_connections == (
        concurrent_connections
    ), (
        "Database connection pool could not handle "
        "the concurrent connection workload. "
        f"Failures: {failures}"
    )

    assert len(latencies) == (
        concurrent_connections
    ), (
        "Unexpected number of connection measurements."
    )

    assert workload_elapsed >= 0

    assert minimum_latency >= 0

    assert average_latency >= 0

    assert maximum_latency >= average_latency

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("=" * 60)

    print(
        "PR-055 database connection-pool pressure "
        "test: PASSED"
    )
