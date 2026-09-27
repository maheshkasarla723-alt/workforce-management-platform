# ============================================================
# PR-054 - WORST-CASE PAYLOAD / MEMORY MEASUREMENT TEST
# ============================================================

import json
import time
import tracemalloc

from tests.test_api import create_test_admin, create_test_employee


def test_employee_api_worst_case_payload_memory(
    client,
    db_session,
):
    """
    PR-054

    Measure memory and payload size when the employee API returns
    its maximum supported page size.

    The employee-list API returns a JSON LIST, not a JSON object.

    Test goals:
    - Create a realistic maximum-size employee dataset.
    - Request the maximum employee page size.
    - Verify the API returns JSON successfully.
    - Measure serialized response payload size.
    - Measure Python memory allocated while processing the response.
    - Measure request latency.
    """

    print("\n")
    print("=" * 60)
    print("PR-054 WORST-CASE PAYLOAD / MEMORY TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    maximum_page_size = 100

    # Safety thresholds for this local production-readiness test.
    # These are deliberately generous so the test detects abnormal
    # memory/payload growth without requiring unrealistic limits.
    maximum_payload_mb = 5.0
    maximum_memory_growth_mb = 50.0
    maximum_latency_seconds = 2.0

    # --------------------------------------------------------
    # Create authenticated Admin
    # --------------------------------------------------------

    token = create_test_admin(
        client,
        db_session,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # --------------------------------------------------------
    # Create enough employees to fill the maximum page.
    #
    # create_test_employee() creates real Employee records with:
    # name, email, age and salary.
    # --------------------------------------------------------

    for _ in range(maximum_page_size):
        create_test_employee(db_session)

    db_session.commit()

    # --------------------------------------------------------
    # Start memory tracing
    # --------------------------------------------------------

    tracemalloc.start()

    current_before, peak_before = tracemalloc.get_traced_memory()

    # --------------------------------------------------------
    # Execute maximum-size employee API request
    # --------------------------------------------------------

    request_start = time.perf_counter()

    response = client.get(
        f"/api/employees/?page=1&limit={maximum_page_size}",
        headers=headers,
    )

    request_latency = (
        time.perf_counter() - request_start
    )

    current_after, peak_after = tracemalloc.get_traced_memory()

    tracemalloc.stop()

    # --------------------------------------------------------
    # API status
    # --------------------------------------------------------

    assert response.status_code == 200, (
        "Employee API did not successfully return the "
        "maximum page-size payload."
    )

    # --------------------------------------------------------
    # Validate JSON payload
    #
    # IMPORTANT:
    # The real employee endpoint returns a LIST.
    # --------------------------------------------------------

    payload = response.json()

    assert isinstance(payload, list), (
        "Employee API payload must be a JSON list."
    )

    assert len(payload) == maximum_page_size, (
        f"Expected {maximum_page_size} employees, "
        f"received {len(payload)}."
    )

    # --------------------------------------------------------
    # Validate each employee payload
    # --------------------------------------------------------

    for employee in payload:

        assert isinstance(employee, dict), (
            "Each employee item must be a JSON object."
        )

        assert "id" in employee
        assert "name" in employee
        assert "email" in employee
        assert "age" in employee
        assert "salary" in employee

    # --------------------------------------------------------
    # Measure serialized JSON payload size
    # --------------------------------------------------------

    serialized_payload = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    payload_bytes = len(serialized_payload)
    payload_mb = payload_bytes / (
        1024 * 1024
    )

    # --------------------------------------------------------
    # Measure traced Python memory growth
    # --------------------------------------------------------

    memory_growth_bytes = max(
        0,
        current_after - current_before,
    )

    memory_growth_mb = (
        memory_growth_bytes
        / (1024 * 1024)
    )

    peak_memory_bytes = max(
        0,
        peak_after - peak_before,
    )

    peak_memory_mb = (
        peak_memory_bytes
        / (1024 * 1024)
    )

    # --------------------------------------------------------
    # Output measurements
    # --------------------------------------------------------

    print()
    print(
        f"Requested employees : "
        f"{maximum_page_size}"
    )

    print(
        f"Returned employees  : "
        f"{len(payload)}"
    )

    print(
        f"Payload size        : "
        f"{payload_bytes / 1024:.2f} KB"
    )

    print(
        f"Payload size        : "
        f"{payload_mb:.4f} MB"
    )

    print(
        f"Memory growth       : "
        f"{memory_growth_mb:.4f} MB"
    )

    print(
        f"Peak traced memory  : "
        f"{peak_memory_mb:.4f} MB"
    )

    print(
        f"Request latency     : "
        f"{request_latency:.4f}s"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Production-readiness assertions
    # --------------------------------------------------------

    assert payload_bytes > 0, (
        "Employee API returned an empty serialized payload."
    )

    assert payload_mb <= maximum_payload_mb, (
        "Worst-case employee API payload exceeded the "
        f"{maximum_payload_mb:.1f} MB safety threshold: "
        f"{payload_mb:.4f} MB"
    )

    assert memory_growth_mb <= maximum_memory_growth_mb, (
        "Memory growth exceeded the "
        f"{maximum_memory_growth_mb:.1f} MB safety threshold: "
        f"{memory_growth_mb:.4f} MB"
    )

    assert request_latency <= maximum_latency_seconds, (
        "Worst-case employee API request exceeded the "
        f"{maximum_latency_seconds:.1f}-second threshold: "
        f"{request_latency:.4f}s"
    )

    print(
        "PR-054 worst-case payload memory measurement: PASSED"
    )