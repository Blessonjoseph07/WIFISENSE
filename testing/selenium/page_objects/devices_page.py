"""
Devices & Service Desk Page Object
Encapsulates node fleet table, node provisioning modal, MAC address generation, and fault report ticketing.
"""
import time
from selenium.webdriver.common.by import By
from testing.selenium.page_objects.base_page import BasePage

class DevicesPage(BasePage):
    # Locators
    PROVISION_NODE_BTN = (By.XPATH, "//button[contains(., 'Provision Node') or contains(., 'Register Device') or contains(., 'Add Device')]")
    MAC_INPUT = (By.XPATH, "//label[contains(., 'MAC')]/following-sibling::input | //input[contains(@placeholder, 'AA:BB:CC') or @name='mac']")
    DEVICE_ROOM_SELECT = (By.XPATH, "//select[contains(@name, 'room') or contains(@id, 'room')]")
    SUBMIT_PROVISION_BTN = (By.XPATH, "//button[@type='submit' and (contains(., 'Save') or contains(., 'Register') or contains(., 'Provision'))]")
    TOKEN_MODAL = (By.XPATH, "//*[contains(., 'Device Authentication Token') or contains(., 'Bearer Token')]")
    REPORT_FAULT_BTN = (By.XPATH, "//button[contains(., 'Report Fault') or contains(., 'File Ticket')]")
    FAULT_DESC_INPUT = (By.XPATH, "//textarea[contains(@placeholder, 'Describe') or contains(@placeholder, 'fault')]")
    SUBMIT_FAULT_BTN = (By.XPATH, "//button[contains(., 'Submit Report') or contains(., 'File Report')]")

    def open_devices_view(self, shell):
        shell.navigate_to_view("devices")
        time.sleep(1)

    def provision_new_device(self, mac_address="C4:4F:33:18:99:99"):
        if self.is_visible(*self.PROVISION_NODE_BTN, timeout=4):
            self.click(*self.PROVISION_NODE_BTN)
            time.sleep(0.5)
            if self.is_visible(*self.MAC_INPUT, timeout=4):
                self.type_text(*self.MAC_INPUT, mac_address)
                if self.is_visible(*self.SUBMIT_PROVISION_BTN, timeout=3):
                    self.click(*self.SUBMIT_PROVISION_BTN)
                    time.sleep(1)
                    return True
        return False

    def report_node_fault(self, description="Intermittent CSI packet loss observed during morning telemetry stream."):
        fault_btns = self.find_all(*self.REPORT_FAULT_BTN)
        if fault_btns:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fault_btns[0])
            fault_btns[0].click()
            time.sleep(0.5)
            if self.is_visible(*self.FAULT_DESC_INPUT, timeout=3):
                self.type_text(*self.FAULT_DESC_INPUT, description)
                if self.is_visible(*self.SUBMIT_FAULT_BTN, timeout=3):
                    self.click(*self.SUBMIT_FAULT_BTN)
                    time.sleep(1)
                    return True
        return False
