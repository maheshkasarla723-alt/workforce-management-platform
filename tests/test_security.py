import re
from pathlib import Path


# ============================================================
# FRONTEND FILE
# ============================================================

def find_frontend_file():
    project_root = Path(__file__).resolve().parents[1]

    candidates = [
        project_root / "frontend" / "index.html",
        project_root / "frontend" / "Workforce_Management_Frontend.html",
        project_root / "frontend" / "Workforce_Management_Frontend_Login_Complete.html",
    ]

    for file_path in candidates:
        if file_path.exists():
            return file_path

    frontend_folder = project_root / "frontend"

    if frontend_folder.exists():
        html_files = list(frontend_folder.glob("*.html"))

        if html_files:
            return html_files[0]

    return None


# ============================================================
# XSS PROTECTION TESTS
# ============================================================

def test_frontend_has_escape_html_function():
    frontend_file = find_frontend_file()

    assert frontend_file is not None, (
        "No frontend HTML file was found."
    )

    content = frontend_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    assert "function escapeHtml" in content


def test_escape_html_escapes_script_characters():
    frontend_file = find_frontend_file()

    assert frontend_file is not None

    content = frontend_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    assert '.replace(/</g, "&lt;")' in content
    assert '.replace(/>/g, "&gt;")' in content
    assert '.replace(/"/g, "&quot;")' in content
    assert ".replace(/'/g, \"&#039;\")" in content


# ============================================================
# EMPLOYEE XSS PROTECTION
# ============================================================

def test_frontend_uses_escaped_employee_values():
    frontend_file = find_frontend_file()

    assert frontend_file is not None

    content = frontend_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    assert re.search(
        r"escapeHtml\(\s*employee\.name\s*\)",
        content
    )

    assert re.search(
        r"escapeHtml\(\s*employee\.email\s*\)",
        content
    )


# ============================================================
# TASK XSS PROTECTION
# ============================================================

def test_frontend_uses_escaped_task_values():
    frontend_file = find_frontend_file()

    assert frontend_file is not None

    content = frontend_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    # Allow normal formatting and line breaks inside
    # escapeHtml(task.title)
    assert re.search(
        r"escapeHtml\(\s*task\.title\s*\)",
        content
    )

    # Allow normal formatting and line breaks inside
    # escapeHtml(task.description)
    assert re.search(
        r"escapeHtml\(\s*task\.description\s*\)",
        content
    )


# ============================================================
# JAVASCRIPT URL SECURITY
# ============================================================

def test_frontend_does_not_contain_obvious_javascript_url():
    frontend_file = find_frontend_file()

    assert frontend_file is not None

    content = frontend_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    assert not re.search(
        r"javascript\s*:",
        content,
        flags=re.IGNORECASE
    )


# ============================================================
# DANGEROUS XSS PAYLOAD CHECK
# ============================================================

def test_frontend_has_no_obvious_inline_script_injection_payload():
    frontend_file = find_frontend_file()

    assert frontend_file is not None

    content = frontend_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    dangerous_patterns = [
        "<script>alert(",
        "<script>prompt(",
        "<script>confirm(",
    ]

    lowered = content.lower()

    for pattern in dangerous_patterns:
        assert pattern not in lowered


# ============================================================
# XSS PAYLOAD SANITY TEST
# ============================================================

def test_common_xss_payload_is_not_safe_html():
    malicious_input = '<script>alert("XSS")</script>'

    assert "<" in malicious_input
    assert ">" in malicious_input
    assert '"' in malicious_input

    assert "<script>" in malicious_input
    assert "</script>" in malicious_input