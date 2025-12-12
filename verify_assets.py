
import os
import sys
from playwright.sync_api import sync_playwright

def verify_assets():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Load the file
        file_path = os.path.abspath("index.html")
        page.goto(f"file://{file_path}")

        # 1. Verify Favicon
        # We look for <link rel="icon" ...>
        # Note: Playwright might not "see" the favicon in the viewport, but we can check the DOM.
        favicon_element = page.locator('link[rel="icon"]')
        if favicon_element.count() > 0:
            href = favicon_element.first.get_attribute('href')
            if href and href.startswith('data:image/png;base64,'):
                print("SUCCESS: Favicon link found with Base64 href.")
            else:
                print(f"FAILURE: Favicon link found but href is invalid or missing. Href start: {href[:30] if href else 'None'}")
        else:
            print("FAILURE: Favicon link tag not found.")

        # 2. Verify Logo
        # The logo was inserted into <header class="text-center mb-8">
        # We look for an img inside header with alt="Logo Generator Artikel" (based on my injection script)
        # OR just an img with base64 src in the header if I used a different alt.
        # Let's check the injection script logic:
        # f'<img src="data:image/png;base64,{logo_b64}" alt="Logo Generator Artikel" class="mx-auto mb-4 w-24 h-auto">'

        logo_element = page.locator('header.text-center img[alt="Logo Generator Artikel"]')
        if logo_element.count() > 0:
            src = logo_element.first.get_attribute('src')
            if src and src.startswith('data:image/png;base64,'):
                print("SUCCESS: Logo image found with Base64 src.")
                # Verify visibility
                if logo_element.first.is_visible():
                     print("SUCCESS: Logo image is visible.")
                else:
                     print("WARNING: Logo image exists but might not be visible (check css).")
            else:
                print(f"FAILURE: Logo image found but src is invalid. Src start: {src[:30] if src else 'None'}")
        else:
            print("FAILURE: Logo image tag not found in header.")

        browser.close()

if __name__ == "__main__":
    verify_assets()
