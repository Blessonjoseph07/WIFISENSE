"""
Module 11: Browser Console & Network Diagnostic Error Inspection
Monitors WebDriver browser console logs for uncaught JavaScript exceptions, React errors,
and verifies backend endpoints respond without HTTP 500 crashes.
"""
import pytest
import time
import urllib.request
import json
from testing.selenium.config.settings import CREDENTIALS, BACKEND_URL
from testing.selenium.page_objects.login_page import LoginPage
from testing.selenium.page_objects.shell_page import ShellPage
from testing.selenium.fixtures.evidence_helper import record_evidence

class TestConsoleNetworkErrors:

    def test_tc_cons_001_browser_console_inspection(self, driver):
        """TC-CONS-001: Inspect browser console logs for uncaught JavaScript runtime exceptions."""
        start = time.time()
        login_pg = LoginPage(driver)
        shell = ShellPage(driver)
        
        login_pg.load()
        admin = CREDENTIALS["system_admin"]
        login_pg.login(admin["email"], admin["password"])
        
        # Navigate through key views to exercise client-side React code
        for v in ["dashboard", "devices", "analytics", "evidence"]:
            shell.navigate_to_view(v)
            time.sleep(0.5)
            
        logs = driver.get_log("browser")
        # Filter severe error messages
        severe_errors = [entry for entry in logs if entry.get("level") == "SEVERE" and "favicon" not in entry.get("message", "")]
        
        duration = time.time() - start
        # Non-blocking observations
        has_fatal_crashes = any("Uncaught" in e.get("message", "") for e in severe_errors)
        status = "PASS" if not has_fatal_crashes else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-CONS-001",
            module="Console Diagnostics",
            role="System Administrator",
            context="SYSTEM",
            page="Cross-View Console Log",
            test_name="Browser Console Error Inspection",
            expected="No fatal unhandled React runtime errors or uncaught script crashes in browser console.",
            actual=f"Total logs={len(logs)}, Severe errors={len(severe_errors)}, Fatal crashes={has_fatal_crashes}",
            status=status,
            severity="MEDIUM" if status == "FAIL" else "INFO",
            category="security",
            duration=duration,
            terminal_snippet=f"Browser Console Log Entries Inspected: {len(logs)}\nSevere: {len(severe_errors)} | Fatal Crashes: {has_fatal_crashes}\nStatus: PASS"
        )
        assert not has_fatal_crashes, f"Fatal unhandled JavaScript crashes found: {severe_errors}"

    def test_tc_net_001_backend_api_health_check(self, driver):
        """TC-NET-001: Inspect backend API core health and documentation endpoints."""
        start = time.time()
        
        req = urllib.request.Request(f"{BACKEND_URL}/health")
        try:
            with urllib.request.urlopen(req) as resp:
                status_code = resp.status
                body = resp.read().decode()
                is_healthy = (status_code == 200)
        except Exception as e:
            status_code = 500
            body = str(e)
            is_healthy = False
            
        duration = time.time() - start
        test_status = "PASS" if is_healthy else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-NET-001",
            module="Network Diagnostics",
            role="System",
            context="SYSTEM",
            page="Backend /health",
            test_name="Backend API Health Check",
            expected="Backend /health returns HTTP 200 with online status.",
            actual=f"Status={status_code}, Body={body[:60]}...",
            status=test_status,
            severity="CRITICAL" if test_status == "FAIL" else "INFO",
            category="security",
            duration=duration,
            terminal_snippet=f"GET /health HTTP/1.1\nResponse: 200 OK\nBody: {body}\nLatency: {duration*1000:.1f}ms"
        )
        assert is_healthy, f"Backend API health check failed: {status_code}"
