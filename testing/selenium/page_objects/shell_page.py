"""
Application Shell Page Object
Encapsulates navigation menus, role badges, view switching, header controls,
fall alert banner interactions, and RBAC visibility checks across all app contexts.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from testing.selenium.page_objects.base_page import BasePage

class ShellPage(BasePage):
    # Common Header / Sidebar Locators
    ROLE_BADGE = (By.XPATH, "//span[contains(@class, 'font-mono') and (contains(., 'CARE') or contains(., 'SPACE') or contains(., 'SYSTEM') or contains(., 'FAMILY'))]")
    ORG_HEADER = (By.XPATH, "//div[contains(@class, 'text-xs') and (contains(., 'St. Peter') or contains(., 'Amal Jyothi') or contains(., 'Enterprise') or contains(., 'Organization'))]")
    USER_IDENTITY = (By.XPATH, "//*[contains(@class, 'font-semibold') and (contains(., 'Blesson') or contains(., 'Mary') or contains(., 'Elizabeth') or contains(., 'Abhinand') or contains(., 'Tomy') or contains(., 'John'))]")
    
    # Emergency Fall Alert Banner / Siren Modal
    FALL_BANNER = (By.XPATH, "//*[contains(., 'FALL DETECTED') or contains(., 'CRITICAL FALL ALARM')]")
    ACKNOWLEDGE_BTN = (By.XPATH, "//button[contains(., 'Acknowledge') or contains(., 'ACKNOWLEDGE')]")
    RESOLVE_BTN = (By.XPATH, "//button[contains(., 'Resolve') or contains(., 'RESOLVE')]")
    
    # Toast Notification
    TOAST_ALERT = (By.XPATH, "//div[contains(@class, 'shadow-lg') and (contains(., 'Access Denied') or contains(., 'Success') or contains(., 'Warning') or contains(., 'Error'))]")

    def get_role_badge_text(self):
        if self.is_visible(*self.ROLE_BADGE, timeout=4):
            return self.get_text(*self.ROLE_BADGE)
        return ""

    def get_displayed_user_name(self):
        if self.is_visible(*self.USER_IDENTITY, timeout=4):
            return self.get_text(*self.USER_IDENTITY)
        return ""

    def navigate_to_view(self, view_id):
        """Click on navigation menu item by view ID or label."""
        # Find button with data-view or label or icon corresponding to the view
        xpath = f"//button[@data-view='{view_id}' or contains(@data-testid, '{view_id}') or contains(@id, '{view_id}')]"
        elems = self.find_all(By.XPATH, xpath)
        if not elems:
            # Fallback by text matching known view labels
            label_map = {
                "dashboard": "Monitoring Dashboard",
                "caregiver": "Elder Care",
                "residents": "Resident Directory",
                "corporate": "Corporate Workplace",
                "occupancy": "Room Occupancy",
                "assets": "Facility & Assets",
                "devices": "Devices & Service Desk",
                "alerts": "Alerts & Incidents",
                "analytics": "Analytics & Telemetry",
                "orgadmin": "Staff & Organization",
                "sysadmin": "System Admin",
                "profile": "My Profile",
                "sharing_policies": "Sharing Policies",
                "doctor": "Medical Portal",
                "sensing": "Sensing Monitor",
                "providers": "Medical Providers",
                "evidence": "Evidence & Limits",
                "bookings": "Room Scheduling",
                "family": "Family Portal"
            }
            lbl = label_map.get(view_id, view_id)
            xpath = f"//button[contains(., '{lbl}') or contains(@title, '{lbl}')]"
            elems = self.find_all(By.XPATH, xpath)

        if elems:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elems[0])
            try:
                elems[0].click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", elems[0])
            time.sleep(1)
            return True
        return False

    def is_view_rendered(self, view_id):
        """Verify view root container or key component is displayed."""
        time.sleep(0.5)
        # Check text or unique elements of each view
        indicators = {
            "dashboard": ["Room Overview", "CSI 3D SENSING", "Central Monitoring", "Live Telemetry", "Signal Stream"],
            "caregiver": ["Elder Care & Safety", "Resident Health Status", "Shift Log", "Clinical Details"],
            "residents": ["Resident Directory", "Resident Profiles", "Care Plans", "Room 101"],
            "corporate": ["Corporate Workplace", "Workstation Occupancy", "HVAC", "Meeting Rooms"],
            "occupancy": ["Room Occupancy View", "Occupancy status across all rooms", "Occupied", "Vacant"],
            "assets": ["Facility & Assets", "Building Hierarchy", "Floors", "Add Building"],
            "devices": ["Devices & Service Desk", "Wi-Fi Sensing Node", "Provision Node", "MAC Address", "Fault"],
            "alerts": ["Alerts & Incidents", "Critical Fall Queue", "Active Alarms", "Resolved Incidents"],
            "analytics": ["Analytics & Telemetry", "Occupancy Heatmap", "CSI Telemetry Trends", "Classification"],
            "orgadmin": ["Staff & Organization", "Access Policies", "Organization Links", "Staff Management"],
            "sysadmin": ["System Admin Console", "Multi-Tenant", "Global System Health", "Organization Oversight"],
            "profile": ["My Profile", "Account Settings", "Email Address", "First Name"],
            "sharing_policies": ["Sharing Policies", "Family Data Sharing", "Privacy Policy", "Strict Privacy"],
            "doctor": ["Medical Portal", "Doctor Portal", "Assigned Residents", "Consultations"],
            "providers": ["Medical Providers", "Doctor Approvals", "Provider Directory"],
            "evidence": ["Evidence & Limits", "Scientific Baseline", "CSI Sensing Boundaries"],
            "bookings": ["Room Scheduling", "Upcoming Meetings", "Book Corporate Room"],
            "family": ["Family Portal", "Resident Safety Status", "Safety Log", "Subscription"]
        }
        keywords = indicators.get(view_id, [view_id])
        page_source = self.driver.page_source
        return any(kw in page_source for kw in keywords)

    def is_access_denied_toast_shown(self):
        if self.is_visible(*self.TOAST_ALERT, timeout=3):
            text = self.get_text(*self.TOAST_ALERT)
            return "Access Denied" in text or "not available" in text
        return False
