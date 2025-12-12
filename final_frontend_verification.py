import os
import json
from playwright.sync_api import sync_playwright, expect

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Load the page
        page.goto(f"file://{os.path.abspath('index.html')}")

        # Set API Key to bypass modal
        page.evaluate("localStorage.setItem('geminiApiKey', 'dummy-key')")
        page.reload()

        # 1. Verify Dark Mode
        print("Toggling Dark Mode...")
        page.click("#theme-toggle-btn")
        page.wait_for_timeout(500) # Wait for transition
        page.screenshot(path="verification/dark_mode.png")
        print("Dark Mode screenshot taken.")

        # 2. Verify Error Dialog
        print("Triggering Error Dialog...")

        # Fill required fields
        page.fill("#topic", "Test Topic")

        # Add a website URL to trigger extraction
        page.click("button[onclick=\"addReferenceInput('website')\"]")
        page.fill("input[name='url_website']", "https://example.com")

        # Mock failures
        page.route("**/*", lambda route: route.abort("failed") if "api" in route.request.url or "corsproxy" in route.request.url else route.continue_())

        # Click Generate
        # We need to handle the alert dialog by capturing its message
        dialog_message = []
        page.on("dialog", lambda dialog: dialog_message.append(dialog.message) or dialog.accept())

        page.click("#generate-btn")

        # Wait for the processing to hit the error
        expect(page.locator("#loading-modal-overlay")).to_be_hidden(timeout=5000)

        print(f"Dialog Message: {dialog_message}")

        # Inject the message into the DOM for the screenshot
        if dialog_message:
            msg = json.dumps(dialog_message[0]) # JSON Encode to handle newlines and quotes
            page.evaluate(f"document.body.innerHTML += '<div id=debug-alert style=position:fixed;top:0;left:0;background:red;color:white;z-index:9999;padding:20px;white-space:pre-wrap;>' + {msg} + '</div>'")

        page.screenshot(path="verification/error_dialog.png")
        print("Error Dialog screenshot taken.")

        browser.close()

if __name__ == "__main__":
    os.makedirs("verification", exist_ok=True)
    run()
