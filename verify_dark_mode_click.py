
import os
import time
from playwright.sync_api import sync_playwright

def verify_dark_mode_click():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context()
        page = context.new_page()

        # Load the file
        file_path = os.path.abspath("index.html")

        # Pre-set localStorage to avoid API modal
        page.add_init_script("""
            localStorage.setItem('geminiApiKey', 'dummy-key');
        """)

        page.goto(f"file://{file_path}")

        # Wait for page load
        page.wait_for_load_state("networkidle")

        # Check initial state
        is_dark = page.evaluate("document.documentElement.classList.contains('dark')")
        print(f"Initial dark class presence: {is_dark}")

        # If it's dark initially (from OS preference?), switch to light first
        if is_dark:
            print("Initial state is Dark. Clicking toggle to switch to Light.")
            page.click("#theme-toggle-btn")
            time.sleep(1)
            is_dark_after = page.evaluate("document.documentElement.classList.contains('dark')")
            if is_dark_after:
                print("FAIL: Failed to switch to Light mode.")
            else:
                print("Switched to Light mode.")

        # Now click to switch to Dark Mode
        print("Clicking toggle to switch to Dark Mode.")
        page.click("#theme-toggle-btn")
        time.sleep(1)

        # Check class
        has_class = page.evaluate("document.documentElement.classList.contains('dark')")
        if not has_class:
            print("FAIL: 'dark' class not added to html element.")
        else:
            print("PASS: 'dark' class added.")

        # Check computed background color
        # We expect dark mode background (gray-900 is rgb(17, 24, 39))
        bg_color = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
        print(f"Body background color in dark mode: {bg_color}")

        # Check tailwind config
        tailwind_config = page.evaluate("window.tailwind.config")
        print(f"Tailwind config: {tailwind_config}")

        # Take screenshot
        page.screenshot(path="verify_dark_mode_click.png")
        print("Screenshot saved.")

        browser.close()

if __name__ == "__main__":
    verify_dark_mode_click()
