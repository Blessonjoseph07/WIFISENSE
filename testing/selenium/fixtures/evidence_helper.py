"""
Evidence recording helper for Wi-Fi Sense Selenium tests
Synchronizes screenshot captures, execution metrics, and terminal logs for report synthesis.
"""
import time
from pathlib import Path
from testing.selenium.config.settings import SCREENSHOT_DIR, TERMINAL_DIR
from testing.selenium.fixtures.conftest import TEST_RECORDS

def record_evidence(
    driver,
    test_id,
    module,
    role,
    context,
    page,
    test_name,
    expected,
    actual,
    status="PASS",
    severity="INFO",
    category="authentication",
    duration=0.0,
    terminal_snippet="",
    error_message=""
):
    screenshot_filename = f"{test_id.replace('-', '_')}_{test_name.lower().replace(' ', '_')[:30]}.png"
    cat_dir = SCREENSHOT_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = cat_dir / screenshot_filename
    
    try:
        driver.save_screenshot(str(screenshot_path))
    except Exception as e:
        print(f"Warning: Screenshot capture failed for {test_id}: {e}")

    # Write terminal log for this specific test case
    term_file = TERMINAL_DIR / f"{test_id.lower().replace('-', '_')}.txt"
    with open(term_file, "w", encoding="utf-8") as f:
        f.write(f"=== TEST EXECUTION LOG: {test_id} ===\n")
        f.write(f"Test Name: {test_name}\n")
        f.write(f"Module: {module} | Role: {role} | Context: {context}\n")
        f.write(f"Status: {status} | Severity: {severity}\n")
        f.write(f"Expected: {expected}\n")
        f.write(f"Actual: {actual}\n")
        f.write(f"Screenshot: {screenshot_filename}\n")
        f.write(f"Duration: {duration:.2f}s\n")
        if error_message:
            f.write(f"Error: {error_message}\n")
        if terminal_snippet:
            f.write("\n--- Terminal / API Trace ---\n")
            f.write(terminal_snippet + "\n")

    record = {
        "test_id": test_id,
        "module": module,
        "role": role,
        "context": context,
        "page": page,
        "test_name": test_name,
        "expected": expected,
        "actual": actual,
        "status": status,
        "severity": severity,
        "duration_sec": round(duration, 2),
        "category": category,
        "screenshot": str(screenshot_path),
        "screenshot_rel": f"testing/screenshots/{category}/{screenshot_filename}",
        "screenshot_name": screenshot_filename,
        "terminal_log": str(term_file),
        "terminal_snippet": terminal_snippet or f"Executing {test_id} - {test_name}\nStatus: {status}",
        "error_message": error_message
    }
    TEST_RECORDS.append(record)
    return record
