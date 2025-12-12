import os
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

        # Check configuration
        config_defined = page.evaluate("typeof tailwind.config !== 'undefined'")
        print(f"Tailwind config defined: {config_defined}")

        if not config_defined:
            print("FAIL: tailwind.config is not defined.")
            browser.close()
            return

        dark_mode_setting = page.evaluate("tailwind.config.darkMode")
        print(f"Tailwind config darkMode: {dark_mode_setting}")

        if dark_mode_setting != 'class':
             print("FAIL: tailwind.config.darkMode is not 'class'.")

        # Toggle Dark Mode
        toggle_btn = page.locator('#theme-toggle-btn')
        toggle_btn.click() # Should turn dark

        # Verify body class
        body = page.locator('body')
        expect(body).to_have_class(re.compile(r'dark'))

        # Verify computed background color
        # dark:bg-gray-900 is #111827 or rgb(17, 24, 39)
        bg_color = body.evaluate("element => getComputedStyle(element).backgroundColor")
        print(f"Body background color in dark mode: {bg_color}")

        if '17, 24, 39' in bg_color or 'rgb(17, 24, 39)' in bg_color:
            print("PASS: Dark mode background color applied.")
        else:
            print(f"FAIL: Dark mode background color mismatch. Expected rgb(17, 24, 39), got {bg_color}")

        # Verify Editor styling in dark mode
        # dark:bg-gray-200 is #e5e7eb or rgb(229, 231, 235)
        editor = page.locator('#article-output')
        # Ensure editor is visible or we check its computed style anyway
        editor_bg = editor.evaluate("element => getComputedStyle(element).backgroundColor")
        print(f"Editor background color in dark mode: {editor_bg}")

        if '229, 231, 235' in editor_bg:
             print("PASS: Editor background color is light gray in dark mode.")
        else:
             print(f"FAIL: Editor background color mismatch. Expected rgb(229, 231, 235), got {editor_bg}")

        browser.close()

import re
if __name__ == "__main__":
    test_dark_mode_fix()
