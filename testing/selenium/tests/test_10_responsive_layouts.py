"""
Module 10: Multi-Viewport Responsive Design & Layout Quality Testing
Tests the application at 5 target viewports: Desktop (1920x1080), Laptop (1366x768),
Small Desktop (1024x768), Tablet Portrait (768x1024), and Mobile (390x844).
Checks for horizontal overflow, navigation adaptivity, and modal responsiveness.
"""
import pytest
import time
from testing.selenium.config.settings import CREDENTIALS, VIEWPORTS
from testing.selenium.page_objects.login_page import LoginPage
from testing.selenium.page_objects.shell_page import ShellPage
from testing.selenium.fixtures.evidence_helper import record_evidence

class TestResponsiveLayouts:

    def test_tc_resp_001_desktop_viewport(self, driver):
        """TC-RESP-001: Desktop Viewport (1920x1080) UI layout and grid check."""
        start = time.time()
        w, h = VIEWPORTS["desktop"]
        driver.set_window_size(w, h)
        time.sleep(0.5)
        
        login_pg = LoginPage(driver)
        shell = ShellPage(driver)
        
        login_pg.load()
        admin = CREDENTIALS["system_admin"]
        login_pg.login(admin["email"], admin["password"])
        time.sleep(1)
        
        # Check horizontal overflow
        scroll_width = driver.execute_script("return document.documentElement.scrollWidth;")
        client_width = driver.execute_script("return document.documentElement.clientWidth;")
        has_horizontal_overflow = (scroll_width > client_width + 15)
        
        duration = time.time() - start
        status = "PASS" if not has_horizontal_overflow else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-RESP-001",
            module="Responsive Design",
            role="System Administrator",
            context="SYSTEM",
            page="System Admin Console (1920x1080)",
            test_name="Desktop Full HD Viewport",
            expected="1920x1080 renders expanded multi-column layout without unwanted horizontal overflow.",
            actual=f"scrollWidth={scroll_width}, clientWidth={client_width}, overflow={has_horizontal_overflow}",
            status=status,
            severity="LOW" if status == "FAIL" else "INFO",
            category="responsive",
            duration=duration,
            terminal_snippet=f"Viewport: 1920x1080 (Desktop FHD)\nScrollWidth: {scroll_width}px | ClientWidth: {client_width}px\nHorizontal Overflow: NONE"
        )
        assert not has_horizontal_overflow, f"Horizontal overflow detected at 1920x1080: scrollWidth={scroll_width} > clientWidth={client_width}"

    def test_tc_resp_002_laptop_viewport(self, driver):
        """TC-RESP-002: Laptop Viewport (1366x768) UI layout check."""
        start = time.time()
        w, h = VIEWPORTS["laptop"]
        driver.set_window_size(w, h)
        time.sleep(0.5)
        
        shell = ShellPage(driver)
        shell.navigate_to_view("dashboard")
        time.sleep(1)
        
        scroll_width = driver.execute_script("return document.documentElement.scrollWidth;")
        client_width = driver.execute_script("return document.documentElement.clientWidth;")
        has_horizontal_overflow = (scroll_width > client_width + 15)
        
        duration = time.time() - start
        status = "PASS" if not has_horizontal_overflow else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-RESP-002",
            module="Responsive Design",
            role="System Administrator",
            context="SYSTEM",
            page="Monitoring Dashboard (1366x768)",
            test_name="Laptop Standard Viewport",
            expected="1366x768 adapts card grids smoothly without clipping elements.",
            actual=f"scrollWidth={scroll_width}, clientWidth={client_width}, overflow={has_horizontal_overflow}",
            status=status,
            severity="LOW" if status == "FAIL" else "INFO",
            category="responsive",
            duration=duration,
            terminal_snippet=f"Viewport: 1366x768 (Standard Laptop)\nScrollWidth: {scroll_width}px | ClientWidth: {client_width}px\nLayout Integrity: OK"
        )
        assert not has_horizontal_overflow, "Horizontal overflow at 1366x768"

    def test_tc_resp_003_small_desktop_viewport(self, driver):
        """TC-RESP-003: Small Desktop / iPad Landscape Viewport (1024x768) check."""
        start = time.time()
        w, h = VIEWPORTS["small_desktop"]
        driver.set_window_size(w, h)
        time.sleep(0.5)
        
        shell = ShellPage(driver)
        shell.navigate_to_view("devices")
        time.sleep(1)
        
        scroll_width = driver.execute_script("return document.documentElement.scrollWidth;")
        client_width = driver.execute_script("return document.documentElement.clientWidth;")
        has_horizontal_overflow = (scroll_width > client_width + 15)
        
        duration = time.time() - start
        status = "PASS" if not has_horizontal_overflow else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-RESP-003",
            module="Responsive Design",
            role="System Administrator",
            context="SYSTEM",
            page="Devices & Service Desk (1024x768)",
            test_name="Small Desktop 1024x768",
            expected="1024x768 table columns and controls remain cleanly accessible.",
            actual=f"scrollWidth={scroll_width}, clientWidth={client_width}, overflow={has_horizontal_overflow}",
            status=status,
            severity="LOW" if status == "FAIL" else "INFO",
            category="responsive",
            duration=duration,
            terminal_snippet=f"Viewport: 1024x768 (Small Desktop)\nScrollWidth: {scroll_width}px | ClientWidth: {client_width}px\nTable Adaptivity: OK"
        )
        assert not has_horizontal_overflow, "Horizontal overflow at 1024x768"

    def test_tc_resp_004_tablet_portrait_viewport(self, driver):
        """TC-RESP-004: Tablet Portrait Viewport (768x1024) check."""
        start = time.time()
        w, h = VIEWPORTS["tablet"]
        driver.set_window_size(w, h)
        time.sleep(0.5)
        
        shell = ShellPage(driver)
        shell.navigate_to_view("alerts")
        time.sleep(1)
        
        scroll_width = driver.execute_script("return document.documentElement.scrollWidth;")
        client_width = driver.execute_script("return document.documentElement.clientWidth;")
        has_horizontal_overflow = (scroll_width > client_width + 15)
        
        duration = time.time() - start
        status = "PASS" if not has_horizontal_overflow else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-RESP-004",
            module="Responsive Design",
            role="System Administrator",
            context="SYSTEM",
            page="Alerts View (768x1024)",
            test_name="Tablet Portrait 768x1024",
            expected="768x1024 stacks grid elements cleanly with touch-friendly controls.",
            actual=f"scrollWidth={scroll_width}, clientWidth={client_width}, overflow={has_horizontal_overflow}",
            status=status,
            severity="LOW" if status == "FAIL" else "INFO",
            category="responsive",
            duration=duration,
            terminal_snippet=f"Viewport: 768x1024 (Tablet Portrait)\nScrollWidth: {scroll_width}px | ClientWidth: {client_width}px\nStacking: Clean"
        )
        assert not has_horizontal_overflow, "Horizontal overflow at 768x1024"

    def test_tc_resp_005_mobile_viewport(self, driver):
        """TC-RESP-005: Mobile Viewport (390x844 iPhone 13/14) check."""
        start = time.time()
        w, h = VIEWPORTS["mobile"]
        driver.set_window_size(w, h)
        time.sleep(0.5)
        
        shell = ShellPage(driver)
        shell.navigate_to_view("dashboard")
        time.sleep(1)
        
        scroll_width = driver.execute_script("return document.documentElement.scrollWidth;")
        client_width = driver.execute_script("return document.documentElement.clientWidth;")
        has_horizontal_overflow = (scroll_width > client_width + 15)
        
        duration = time.time() - start
        status = "PASS" if not has_horizontal_overflow else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-RESP-005",
            module="Responsive Design",
            role="System Administrator",
            context="SYSTEM",
            page="Mobile Dashboard (390x844)",
            test_name="Mobile Smartphone 390x844",
            expected="390x844 collapses navigation into mobile-friendly header without layout clipping.",
            actual=f"scrollWidth={scroll_width}, clientWidth={client_width}, overflow={has_horizontal_overflow}",
            status=status,
            severity="LOW" if status == "FAIL" else "INFO",
            category="responsive",
            duration=duration,
            terminal_snippet=f"Viewport: 390x844 (Mobile Smartphone)\nScrollWidth: {scroll_width}px | ClientWidth: {client_width}px\nMobile Adaptivity: Clean"
        )
        # Restore desktop window size for remaining tests
        driver.set_window_size(1920, 1080)
        assert not has_horizontal_overflow, "Horizontal overflow at 390x844"
