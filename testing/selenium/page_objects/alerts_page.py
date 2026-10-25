"""
Alerts & Emergency Response Page Object
Covers alert queue, fall detection notifications, alarm acknowledgements, resolution modal, and resolution audit notes.
"""
import time
from selenium.webdriver.common.by import By
from testing.selenium.page_objects.base_page import BasePage

class AlertsPage(BasePage):
    # Locators
    ALERTS_HEADING = (By.XPATH, "//h2[contains(., 'Alerts & Incidents') or contains(., 'Active Alerts')]")
    SIMULATE_EVENT_BTN = (By.XPATH, "//button[contains(., 'Simulate Event') or contains(., 'Trigger Simulation') or @title='Simulate']")
    ALERT_CARDS = (By.XPATH, "//div[contains(@class, 'rounded') and (contains(., 'FALL') or contains(., 'MOTION') or contains(., 'PRESENCE'))]")
    ACKNOWLEDGE_BTN = (By.XPATH, "//button[contains(., 'Acknowledge') or contains(., 'ACKNOWLEDGE')]")
    RESOLVE_BTN = (By.XPATH, "//button[contains(., 'Resolve') or contains(., 'RESOLVE')]")
    RESOLUTION_NOTES_INPUT = (By.XPATH, "//textarea[contains(@placeholder, 'notes') or contains(@placeholder, 'Resolution') or @name='notes']")
    SUBMIT_RESOLUTION_BTN = (By.XPATH, "//button[contains(., 'Confirm Resolution') or contains(., 'Resolve Alert') or contains(., 'Save Resolution')]")
    RESOLVED_BADGE = (By.XPATH, "//span[contains(., 'RESOLVED') or contains(., 'Resolved')]")
    
    def open_alerts_view(self, shell):
        shell.navigate_to_view("alerts")
        time.sleep(1)

    def get_alert_count(self):
        cards = self.find_all(*self.ALERT_CARDS)
        return len(cards)

    def acknowledge_first_active_alert(self):
        ack_btns = self.find_all(*self.ACKNOWLEDGE_BTN)
        if ack_btns:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ack_btns[0])
            ack_btns[0].click()
            time.sleep(0.8)
            return True
        return False

    def resolve_first_active_alert(self, notes="Resident Annamma checked. Safe and vitals stable."):
        res_btns = self.find_all(*self.RESOLVE_BTN)
        if res_btns:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", res_btns[0])
            res_btns[0].click()
            time.sleep(0.5)
            # Fill resolution notes if modal appears
            if self.is_visible(*self.RESOLUTION_NOTES_INPUT, timeout=3):
                self.type_text(*self.RESOLUTION_NOTES_INPUT, notes)
                if self.is_visible(*self.SUBMIT_RESOLUTION_BTN, timeout=3):
                    self.click(*self.SUBMIT_RESOLUTION_BTN)
                    time.sleep(1)
            return True
        return False
