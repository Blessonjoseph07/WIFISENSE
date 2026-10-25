"""
Login and Landing Page Object for Wi-Fi Sense
Manages the landing splash, authentication form, credential submission, error feedback, and splash transitions.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from testing.selenium.page_objects.base_page import BasePage

class LoginPage(BasePage):
    # Locators
    GET_STARTED_BTN = (By.XPATH, "//button[contains(., 'Get Started')]")
    EMAIL_INPUT = (By.XPATH, "//input[@type='email']")
    PASSWORD_INPUT = (By.XPATH, "//input[@type='password']")
    SIGN_IN_BTN = (By.XPATH, "//button[@type='submit' and contains(., 'Sign In')]")
    REGISTER_LINK = (By.XPATH, "//button[contains(., 'Create new registration')]")
    BACK_TO_SIGN_IN_LINK = (By.XPATH, "//button[contains(., 'Back to Sign In')]")
    REGISTER_SUBMIT_BTN = (By.XPATH, "//button[@type='submit' and contains(., 'Register')]")
    FIRST_NAME_INPUT = (By.XPATH, "//label[contains(., 'First Name')]/following-sibling::input")
    LAST_NAME_INPUT = (By.XPATH, "//label[contains(., 'Last Name')]/following-sibling::input")
    LOGIN_ERROR_BANNER = (By.XPATH, "//div[contains(@class, 'bg-red-50') and contains(@class, 'text-red-600')]")
    
    # Splash / Transition buttons
    ENTER_DASHBOARD_BTN = (By.XPATH, "//button[contains(., 'Enter Dashboard')]")

    def load(self):
        self.navigate("")
        time.sleep(1)
        self.dismiss_splash_to_login()

    def dismiss_splash_to_login(self):
        """If on LandingSplash, click 'Get Started' to reveal login form."""
        if self.is_visible(*self.GET_STARTED_BTN, timeout=3):
            self.click(*self.GET_STARTED_BTN)
            time.sleep(0.5)

    def login(self, email, password):
        self.dismiss_splash_to_login()
        self.wait_for_visible(*self.EMAIL_INPUT, timeout=8)
        self.type_text(*self.EMAIL_INPUT, email)
        self.type_text(*self.PASSWORD_INPUT, password)
        self.click(*self.SIGN_IN_BTN)
        time.sleep(1.2)
        # Handle contextual splash screen if presented
        self.dismiss_context_splash_if_present()

    def dismiss_context_splash_if_present(self):
        """Handle ElderCareSplash or CorporateSplash 'Enter Dashboard' buttons."""
        if self.is_visible(*self.ENTER_DASHBOARD_BTN, timeout=3):
            self.click(*self.ENTER_DASHBOARD_BTN)
            time.sleep(0.8)

    def get_error_message(self):
        if self.is_visible(*self.LOGIN_ERROR_BANNER, timeout=4):
            return self.get_text(*self.LOGIN_ERROR_BANNER)
        return ""

    def toggle_register_view(self):
        self.dismiss_splash_to_login()
        self.click(*self.REGISTER_LINK)
        time.sleep(0.5)

    def toggle_login_view(self):
        self.click(*self.BACK_TO_SIGN_IN_LINK)
        time.sleep(0.5)

    def is_logged_in(self):
        token = self.get_local_storage_item("token")
        return bool(token and len(token) > 20)

    def logout(self):
        # Look for user profile button or logout button
        try:
            # Click logout if visible or trigger storage clear
            logout_btn = self.driver.find_elements(By.XPATH, "//button[contains(., 'Logout') or contains(., 'Sign Out') or @title='Logout']")
            if logout_btn and logout_btn[0].is_displayed():
                logout_btn[0].click()
                time.sleep(0.5)
            else:
                # Click profile menu first
                profile_btn = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'rounded-full') and (contains(., 'Sr.') or contains(., 'Dr.') or contains(., 'Blesson') or contains(., 'Prof.') or contains(., 'John'))]")
                if profile_btn:
                    profile_btn[0].click()
                    time.sleep(0.4)
                    logout_sub = self.driver.find_elements(By.XPATH, "//button[contains(., 'Sign Out') or contains(., 'Logout')]")
                    if logout_sub:
                        logout_sub[0].click()
        except Exception:
            pass
        self.clear_session()
        time.sleep(0.5)
