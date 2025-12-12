import os
import time
from playwright.sync_api import sync_playwright, expect

def test_dark_mode_fix():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--no-sandbox'])
        page = browser.new_page()
        file_path = os.path.abspath('index.html')
        page.goto(f'file://{file_path}')

        # Set API key to bypass modal
        page.evaluate("localStorage.setItem('geminiApiKey', 'dummy')")
        page.reload()

        # Toggle Dark Mode
        toggle_btn = page.locator('#theme-toggle-btn')
        toggle_btn.click()

        # Wait for transition
        time.sleep(1)

        # Verify body class
        body = page.locator('body')
        expect(body).to_have_class(re.compile(r'dark'))

        # Verify computed background color
        bg_color = body.evaluate("element => getComputedStyle(element).backgroundColor")
        print(f"Body background color in dark mode: {bg_color}")

        # rgb(17, 24, 39) is standard Tailwind gray-900.
        # Depending on browser/OS, might vary slightly or be rgba.
        if '17, 24, 39' in bg_color:
            print("PASS: Dark mode background color applied.")
        else:
            print(f"FAIL: Dark mode background color mismatch. Expected rgb(17, 24, 39), got {bg_color}")

        page.screenshot(path='verification_dark_mode_fixed.png', full_page=True)
        print("Screenshot saved.")

        browser.close()

import re
if __name__ == "__main__":
    test_dark_mode_fix()
