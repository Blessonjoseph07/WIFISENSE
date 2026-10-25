"""
Family Portal Page Object
Encapsulates elderly resident safety view, real-time presence indicators, subscription status, and emergency link requests.
"""
import time
from selenium.webdriver.common.by import By
from testing.selenium.page_objects.base_page import BasePage

class FamilyPage(BasePage):
    # Locators
    FAMILY_PORTAL_TITLE = (By.XPATH, "//*[contains(., 'Family Portal') or contains(., 'Resident Safety')]")
    PRESENCE_BADGE = (By.XPATH, "//*[contains(., 'IN ROOM') or contains(., 'AWAY') or contains(., 'RESTING') or contains(., 'SAFE')]")
    SUBSCRIPTION_STATUS = (By.XPATH, "//*[contains(., 'Subscription') or contains(., 'ACTIVE') or contains(., 'Plan')]")
    SAFETY_LOGS = (By.XPATH, "//div[contains(@class, 'rounded') and (contains(., 'Motion') or contains(., 'Movement') or contains(., 'Presence'))]")
    REQUEST_LINK_BTN = (By.XPATH, "//button[contains(., 'Request Link') or contains(., 'Connect Resident')]")

    def open_family_view(self, shell):
        shell.navigate_to_view("family")
        time.sleep(1)

    def is_presence_badge_displayed(self):
        return self.is_visible(*self.PRESENCE_BADGE, timeout=4)

    def is_subscription_status_displayed(self):
        return self.is_visible(*self.SUBSCRIPTION_STATUS, timeout=4)
