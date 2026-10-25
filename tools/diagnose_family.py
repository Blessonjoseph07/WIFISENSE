import sys, os
sys.path.insert(0, os.path.abspath("."))
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from testing.selenium.page_objects.login_page import LoginPage
from testing.selenium.config.settings import CREDENTIALS

opts = Options()
opts.add_argument('--headless=new')
d = webdriver.Chrome(options=opts)
lp = LoginPage(d)
lp.load()
fam = CREDENTIALS['family_member']
lp.login(fam['email'], fam['password'])
time.sleep(2)
print("TITLE:", d.title)
print("ROLE:", d.execute_script("return localStorage.getItem('role');"))
print("CONTEXT:", d.execute_script("return localStorage.getItem('application_context');"))
body = d.find_element('tag name', 'body').text
print("BODY (first 800 chars):")
print(body[:800])
logs = d.get_log("browser")
print("\nBROWSER LOGS:")
for l in logs:
    print(l)
d.quit()
