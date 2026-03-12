from playwright.sync_api import sync_playwright, Page
import subprocess
from dotenv import load_dotenv
import time
import os

load_dotenv()

def login_user(page: Page):
    page.goto("http://localhost:5000/auth/login")

    page.fill("input[name='username']", os.getenv('BOT_USER'))
    page.fill("input[name='password']", os.getenv('BOT_PASSWORD'))
    page.click("button[type='submit']")


def capture_page(url, filename, width, height):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': width, 'height': height})
        login_user(page)

        page.goto(url, wait_until="networkidle")
        page.click("button#sidebarToggle")
        try:
            page.click("button#toggleFilters")
        except:
            pass

        cmd = [
            "shot-scraper", 
            url, 
            "--full-page", 
            "-o", f"static/screenshots/{filename}",
            "--wait", "2000"
        ]
        subprocess.run(cmd)
        
        page.screenshot(path=f'static/screenshots/{filename}', full_page=True)
        
        browser.close()