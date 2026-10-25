"""
Corporate Workplace & Space Management Page Object
Covers workstation matrix, meeting room occupancy, HVAC controls, and room scheduling bookings.
"""
import time
from selenium.webdriver.common.by import By
from testing.selenium.page_objects.base_page import BasePage

class CorporatePage(BasePage):
    # Locators
    CORPORATE_HEADING = (By.XPATH, "//*[contains(., 'Corporate Workplace') or contains(., 'Space Management')]")
    OCCUPANCY_CARDS = (By.XPATH, "//div[contains(@class, 'rounded') and (contains(., 'Room') or contains(., 'Conference') or contains(., 'Lab'))]")
    BOOK_ROOM_BTN = (By.XPATH, "//button[contains(., 'Book') or contains(., 'Reserve Room')]")
    BOOKING_TITLE_INPUT = (By.XPATH, "//input[contains(@placeholder, 'Meeting') or @name='title']")
    SUBMIT_BOOKING_BTN = (By.XPATH, "//button[@type='submit' and (contains(., 'Confirm') or contains(., 'Book'))]")
    CANCEL_BOOKING_BTN = (By.XPATH, "//button[contains(., 'Cancel') and (contains(., 'Meeting') or contains(., 'Booking'))]")
    
    def open_corporate_view(self, shell):
        shell.navigate_to_view("corporate")
        time.sleep(1)

    def open_bookings_view(self, shell):
        shell.navigate_to_view("bookings")
        time.sleep(1)

    def book_meeting_room(self, title="Q4 Strategy Review"):
        if self.is_visible(*self.BOOK_ROOM_BTN, timeout=4):
            self.click(*self.BOOK_ROOM_BTN)
            time.sleep(0.5)
            if self.is_visible(*self.BOOKING_TITLE_INPUT, timeout=3):
                self.type_text(*self.BOOKING_TITLE_INPUT, title)
                if self.is_visible(*self.SUBMIT_BOOKING_BTN, timeout=3):
                    self.click(*self.SUBMIT_BOOKING_BTN)
                    time.sleep(1)
                    return True
        return False
