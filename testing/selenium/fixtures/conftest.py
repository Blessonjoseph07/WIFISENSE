"""
Pytest configuration and test runner fixtures for Wi-Fi Sense
Configures Chrome WebDriver, screenshot capture on every major step/failure,
browser console error collection, and machine-readable JSON/CSV result export.
"""
import pytest
import os
import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from testing.selenium.config.settings import (
    FRONTEND_URL,
    PAGE_LOAD_TIMEOUT,
    IMPLICIT_WAIT,
    REPORT_DIR,
    TERMINAL_DIR,
    SCREENSHOT_DIR
)

# Global accumulator for test results
TEST_RECORDS = []

@pytest.fixture(scope="function")
def driver():
    chrome_options = Options()
    headless_env = os.getenv("HEADLESS", "1")
    if headless_env == "1":
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--ignore-certificate-errors")
    
    # Enable browser console logging
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(IMPLICIT_WAIT)
    
    yield driver
    
    try:
        driver.quit()
    except Exception:
        pass

@pytest.fixture(autouse=True)
def clean_session_before_test(driver):
    """Ensure clean browser storage before and after each test."""
    try:
        driver.get(FRONTEND_URL)
        driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
        driver.execute_script("sessionStorage.setItem('wifisense_booted', 'true');")
    except Exception:
        pass
    yield

def pytest_sessionfinish(session, exitstatus):
    """Save machine-readable test records and terminal execution outputs cumulatively."""
    json_path = REPORT_DIR / "selenium_results.json"
    csv_path = REPORT_DIR / "selenium_results.csv"
    
    existing = []
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
            
    combined_dict = {r["test_id"]: r for r in existing}
    for r in TEST_RECORDS:
        combined_dict[r["test_id"]] = r
    merged = list(combined_dict.values())
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
        
    if merged:
        keys = ["test_id", "module", "role", "context", "page", "test_name", "status", "severity", "duration_sec", "screenshot", "error_message"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in merged:
                row = {k: r.get(k, "") for k in keys}
                writer.writerow(row)
    print(f"\n[Selenium Test Run Complete] {len(merged)} cumulative tests recorded in {json_path}")
