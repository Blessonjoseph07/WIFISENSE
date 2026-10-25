"""
Wi-Fi Sense Selenium Test Automation Configuration
Defines environment settings, URLs, seeded credentials, and directory paths.
"""
import os
from pathlib import Path

# Base Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
TESTING_DIR = ROOT_DIR / "testing"
SCREENSHOT_DIR = TESTING_DIR / "screenshots"
LOG_DIR = TESTING_DIR / "logs"
REPORT_DIR = TESTING_DIR / "reports"
TERMINAL_DIR = TESTING_DIR / "terminal"

# Ensure all artifact directories exist
for folder in [
    SCREENSHOT_DIR / "authentication",
    SCREENSHOT_DIR / "system_admin",
    SCREENSHOT_DIR / "organization_admin",
    SCREENSHOT_DIR / "facility_manager",
    SCREENSHOT_DIR / "caregiver",
    SCREENSHOT_DIR / "corporate_staff",
    SCREENSHOT_DIR / "family_member",
    SCREENSHOT_DIR / "elder_care",
    SCREENSHOT_DIR / "corporate",
    SCREENSHOT_DIR / "security",
    SCREENSHOT_DIR / "alerts",
    SCREENSHOT_DIR / "devices",
    SCREENSHOT_DIR / "analytics",
    SCREENSHOT_DIR / "responsive",
    LOG_DIR,
    REPORT_DIR,
    TERMINAL_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)

# Environment URLs
FRONTEND_URL = os.getenv("WIFISENSE_FRONTEND_URL", "http://127.0.0.1:5173")
BACKEND_URL = os.getenv("WIFISENSE_BACKEND_URL", "http://127.0.0.1:8000")

# Timeouts (seconds)
PAGE_LOAD_TIMEOUT = 25
IMPLICIT_WAIT = 5
EXPLICIT_WAIT = 12

# Seeded Role Credentials
CREDENTIALS = {
    "system_admin": {
        "email": "blesson@wifisense.com",
        "password": "blessonpassword",
        "role": "system_admin",
        "context": "SYSTEM",
        "name": "Blesson Joseph Byju"
    },
    "elder_facility_manager": {
        "email": "elizabeth@wifisense.com",
        "password": "elizabethpassword",
        "role": "facility_manager",
        "context": "ELDER_CARE",
        "name": "Dr. Elizabeth Kurian",
        "organization": "St. Peter's Elder Care Home"
    },
    "caregiver": {
        "email": "mary@wifisense.com",
        "password": "marypassword",
        "role": "caregiver",
        "context": "ELDER_CARE",
        "name": "Sr. Mary Sebastian",
        "organization": "St. Peter's Elder Care Home"
    },
    "corporate_facility_manager": {
        "email": "abhinand@wifisense.com",
        "password": "abhinandpassword",
        "role": "facility_manager",
        "context": "CORPORATE",
        "name": "Abhinand M A",
        "organization": "Amal Jyothi College of Engineering"
    },
    "corporate_staff": {
        "email": "tomy@wifisense.com",
        "password": "tomypassword",
        "role": "corporate_staff",
        "context": "CORPORATE",
        "name": "Prof. Tomy Joseph",
        "organization": "Amal Jyothi College of Engineering"
    },
    "family_member": {
        "email": "john@wifisense.com",
        "password": "johnpassword",
        "role": "family_member",
        "context": "ELDER_CARE",
        "name": "John Smith",
        "organization": "St. Peter's Elder Care Home"
    }
}

# Responsive Viewport Profiles
VIEWPORTS = {
    "desktop": (1920, 1080),
    "laptop": (1366, 768),
    "small_desktop": (1024, 768),
    "tablet": (768, 1024),
    "mobile": (390, 844)
}
