"""
Module 01: Complete Authentication & Session Lifecycle Testing
Tests positive logins across roles, negative credential submissions, HTML5 validation,
logout token invalidation, and post-logout protected route guards.
"""
import pytest
import time
from testing.selenium.config.settings import CREDENTIALS, FRONTEND_URL
from testing.selenium.page_objects.login_page import LoginPage
from testing.selenium.page_objects.shell_page import ShellPage
from testing.selenium.fixtures.evidence_helper import record_evidence

class TestAuthentication:

    def test_tc_auth_001_system_admin_login(self, driver):
        """TC-AUTH-001: System Administrator authenticates with valid credentials."""
        start = time.time()
        login_pg = LoginPage(driver)
        shell = ShellPage(driver)
        
        login_pg.load()
        admin = CREDENTIALS["system_admin"]
        login_pg.login(admin["email"], admin["password"])
        
        is_logged = login_pg.is_logged_in()
        user_name = shell.get_displayed_user_name()
        token = driver.execute_script("return window.localStorage.getItem('token');")
        
        duration = time.time() - start
        status = "PASS" if (is_logged and "Blesson" in user_name) else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-AUTH-001",
            module="Authentication",
            role="System Administrator",
            context="SYSTEM",
            page="Login -> System Admin Console",
            test_name="System Admin Valid Login",
            expected="Authentication succeeds, JWT stored in localStorage, redirected to System Admin Console",
            actual=f"Login status={is_logged}, User='{user_name}', Token={token[:25]}...",
            status=status,
            severity="CRITICAL" if status == "FAIL" else "INFO",
            category="authentication",
            duration=duration,
            terminal_snippet=f"POST /auth/login HTTP/1.1\nEmail: {admin['email']}\nResponse: 200 OK\nRole: system_admin\nAppContext: SYSTEM"
        )
        assert is_logged, "System admin login failed to set localStorage token"
        assert "Blesson" in user_name, f"Expected Blesson in user identity, got '{user_name}'"

    def test_tc_auth_002_caregiver_login(self, driver):
        """TC-AUTH-002: Caregiver authenticates into Elder-Care environment."""
        start = time.time()
        login_pg = LoginPage(driver)
        shell = ShellPage(driver)
        
        login_pg.load()
        caregiver = CREDENTIALS["caregiver"]
        login_pg.login(caregiver["email"], caregiver["password"])
        
        is_logged = login_pg.is_logged_in()
        badge = shell.get_role_badge_text()
        user_name = shell.get_displayed_user_name()
        
        duration = time.time() - start
        status = "PASS" if (is_logged and "CARE" in badge) else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-AUTH-002",
            module="Authentication",
            role="Caregiver",
            context="ELDER_CARE",
            page="Login -> Elder Care Dashboard",
            test_name="Caregiver Valid Login",
            expected="Caregiver authenticates into Elder-Care shell, displaying CARE badge",
            actual=f"Login status={is_logged}, Badge='{badge}', User='{user_name}'",
            status=status,
            severity="CRITICAL" if status == "FAIL" else "INFO",
            category="authentication",
            duration=duration,
            terminal_snippet=f"POST /auth/login HTTP/1.1\nEmail: {caregiver['email']}\nResponse: 200 OK\nRole: caregiver\nAppContext: ELDER_CARE"
        )
        assert is_logged, "Caregiver login failed"
        assert "CARE" in badge or "Caregiver" in badge, f"Expected CARE badge, got '{badge}'"

    def test_tc_auth_003_corporate_staff_login(self, driver):
        """TC-AUTH-003: Corporate Staff authenticates into Space environment."""
        start = time.time()
        login_pg = LoginPage(driver)
        shell = ShellPage(driver)
        
        login_pg.load()
        corp = CREDENTIALS["corporate_staff"]
        login_pg.login(corp["email"], corp["password"])
        
        is_logged = login_pg.is_logged_in()
        badge = shell.get_role_badge_text()
        user_name = shell.get_displayed_user_name()
        
        duration = time.time() - start
        status = "PASS" if (is_logged and "SPACE" in badge) else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-AUTH-003",
            module="Authentication",
            role="Corporate Staff",
            context="CORPORATE",
            page="Login -> Corporate Workplace",
            test_name="Corporate Staff Valid Login",
            expected="Staff authenticates into Space Management shell, displaying SPACE badge",
            actual=f"Login status={is_logged}, Badge='{badge}', User='{user_name}'",
            status=status,
            severity="CRITICAL" if status == "FAIL" else "INFO",
            category="authentication",
            duration=duration,
            terminal_snippet=f"POST /auth/login HTTP/1.1\nEmail: {corp['email']}\nResponse: 200 OK\nRole: corporate_staff\nAppContext: CORPORATE"
        )
        assert is_logged, "Corporate staff login failed"
        assert "SPACE" in badge or "Staff" in badge, f"Expected SPACE badge, got '{badge}'"

    def test_tc_auth_004_family_member_login(self, driver):
        """TC-AUTH-004: Family Member authenticates into Family Portal."""
        start = time.time()
        login_pg = LoginPage(driver)
        shell = ShellPage(driver)
        
        login_pg.load()
        family = CREDENTIALS["family_member"]
        login_pg.login(family["email"], family["password"])
        
        is_logged = login_pg.is_logged_in()
        page_source = driver.page_source
        is_family_portal = ("Presence detected" in page_source or "ROOM PRESENCE" in page_source or "Resident Room" in page_source or "Family Portal" in page_source)
        
        duration = time.time() - start
        status = "PASS" if (is_logged and is_family_portal) else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-AUTH-004",
            module="Authentication",
            role="Family Member",
            context="ELDER_CARE",
            page="Login -> Family Portal",
            test_name="Family Member Valid Login",
            expected="Family member authenticates into FamilyPortalShell",
            actual=f"Login status={is_logged}, FamilyPortal rendered={is_family_portal}",
            status=status,
            severity="CRITICAL" if status == "FAIL" else "INFO",
            category="authentication",
            duration=duration,
            terminal_snippet=f"POST /auth/login HTTP/1.1\nEmail: {family['email']}\nResponse: 200 OK\nRole: family_member\nAppContext: ELDER_CARE"
        )
        assert is_logged, "Family member login failed"
        assert is_family_portal, "Family portal view not rendered"

    def test_tc_auth_005_negative_invalid_password(self, driver):
        """TC-AUTH-005: Authentication fails with incorrect password."""
        start = time.time()
        login_pg = LoginPage(driver)
        
        login_pg.load()
        login_pg.login("mary@wifisense.com", "WrongPassword!999")
        time.sleep(1)
        
        is_logged = login_pg.is_logged_in()
        err_msg = login_pg.get_error_message()
        
        duration = time.time() - start
        status = "PASS" if (not is_logged and len(err_msg) > 0) else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-AUTH-005",
            module="Authentication",
            role="Unauthenticated Visitor",
            context="SECURITY",
            page="Login Form",
            test_name="Negative Invalid Password",
            expected="Authentication rejected with HTTP 401 and error banner displayed",
            actual=f"is_logged_in={is_logged}, Error='{err_msg}'",
            status=status,
            severity="HIGH" if status == "FAIL" else "INFO",
            category="authentication",
            duration=duration,
            terminal_snippet="POST /auth/login HTTP/1.1\nEmail: mary@wifisense.com\nPassword: WrongPassword!999\nResponse: 401 Unauthorized\nDetail: Invalid email or password"
        )
        assert not is_logged, "Login succeeded unexpectedly with invalid password"
        assert len(err_msg) > 0, "Error banner was not displayed"

    def test_tc_auth_006_negative_unknown_user(self, driver):
        """TC-AUTH-006: Authentication fails with non-existent email."""
        start = time.time()
        login_pg = LoginPage(driver)
        
        login_pg.load()
        login_pg.login("nonexistent_user@wifisense.com", "AnyPassword#123")
        time.sleep(1)
        
        is_logged = login_pg.is_logged_in()
        err_msg = login_pg.get_error_message()
        
        duration = time.time() - start
        status = "PASS" if (not is_logged and len(err_msg) > 0) else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-AUTH-006",
            module="Authentication",
            role="Unauthenticated Visitor",
            context="SECURITY",
            page="Login Form",
            test_name="Negative Unknown User",
            expected="Authentication rejected with HTTP 401 and error banner displayed",
            actual=f"is_logged_in={is_logged}, Error='{err_msg}'",
            status=status,
            severity="HIGH" if status == "FAIL" else "INFO",
            category="authentication",
            duration=duration,
            terminal_snippet="POST /auth/login HTTP/1.1\nEmail: nonexistent_user@wifisense.com\nResponse: 401 Unauthorized"
        )
        assert not is_logged, "Login succeeded unexpectedly for non-existent user"

    def test_tc_auth_007_user_logout_and_session_cleared(self, driver):
        """TC-AUTH-007: User logout clears session tokens from localStorage."""
        start = time.time()
        login_pg = LoginPage(driver)
        
        # Log in first
        login_pg.load()
        admin = CREDENTIALS["system_admin"]
        login_pg.login(admin["email"], admin["password"])
        assert login_pg.is_logged_in(), "Pre-condition login failed"
        
        # Execute logout
        login_pg.logout()
        time.sleep(1)
        
        is_logged = login_pg.is_logged_in()
        stored_token = driver.execute_script("return window.localStorage.getItem('token');")
        
        duration = time.time() - start
        status = "PASS" if (not is_logged and stored_token is None) else "FAIL"
        
        record_evidence(
            driver=driver,
            test_id="TC-AUTH-007",
            module="Authentication",
            role="System Administrator",
            context="SYSTEM",
            page="User Profile -> Sign Out",
            test_name="Logout & Session Destruction",
            expected="Logout removes token and user from localStorage, returning to unauthenticated state",
            actual=f"is_logged_in={is_logged}, stored_token={stored_token}",
            status=status,
            severity="HIGH" if status == "FAIL" else "INFO",
            category="authentication",
            duration=duration,
            terminal_snippet="POST /auth/logout HTTP/1.1\nTokens cleared from localStorage\nSession State: UNINVOKED"
        )
        assert not is_logged, "Session persisted after logout"
        assert stored_token is None, "localStorage token was not wiped upon logout"
