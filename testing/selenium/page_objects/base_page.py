"""
Base Page Object for Wi-Fi Sense Selenium Test Suite
Provides core abstractions: explicit waits, DOM interactions, screenshot capture, and console log retrieval.
"""
import time
import os
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from testing.selenium.config.settings import EXPLICIT_WAIT, SCREENSHOT_DIR, FRONTEND_URL

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, EXPLICIT_WAIT)

    def navigate(self, path=""):
        url = f"{FRONTEND_URL}/{path}".rstrip("/")
        self.driver.get(url)
        self.dismiss_boot_screens_if_present()

    def dismiss_boot_screens_if_present(self):
        """Ensure loading animation or landing splash is dismissed if present."""
        try:
            self.driver.execute_script("""
                try {
                    sessionStorage.setItem('wifisense_booted', 'true');
                    sessionStorage.setItem('has_seen_elder_splash', 'true');
                    sessionStorage.setItem('has_seen_corporate_splash', 'true');
                } catch(e) {}
            """)
        except WebDriverException:
            pass

    def wait_for_element(self, by, locator, timeout=EXPLICIT_WAIT):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, locator))
        )

    def wait_for_visible(self, by, locator, timeout=EXPLICIT_WAIT):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, locator))
        )

    def wait_for_clickable(self, by, locator, timeout=EXPLICIT_WAIT):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, locator))
        )

    def find(self, by, locator):
        return self.driver.find_element(by, locator)

    def find_all(self, by, locator):
        return self.driver.find_elements(by, locator)

    def click(self, by, locator, timeout=EXPLICIT_WAIT):
        el = self.wait_for_clickable(by, locator, timeout)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", el)
        try:
            el.click()
        except WebDriverException:
            self.driver.execute_script("arguments[0].click();", el)

    def type_text(self, by, locator, text, clear_first=True, timeout=EXPLICIT_WAIT):
        el = self.wait_for_visible(by, locator, timeout)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        if clear_first:
            el.clear()
        el.send_keys(text)

    def get_text(self, by, locator, timeout=EXPLICIT_WAIT):
        el = self.wait_for_visible(by, locator, timeout)
        return el.text.strip()

    def is_visible(self, by, locator, timeout=3):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, locator))
            ) is not None
        except (TimeoutException, NoSuchElementException):
            return False

    def capture_screenshot(self, filename, category="authentication"):
        cat_dir = SCREENSHOT_DIR / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        filepath = cat_dir / filename
        self.driver.save_screenshot(str(filepath))
        return filepath

    def get_browser_console_logs(self):
        try:
            logs = self.driver.get_log("browser")
            return logs
        except Exception:
            return []

    def set_viewport(self, width, height):
        self.driver.set_window_size(width, height)
        time.sleep(0.3)

    def get_local_storage_item(self, key):
        return self.driver.execute_script(f"return window.localStorage.getItem('{key}');")

    def clear_session(self):
        self.driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
        self.driver.refresh()
