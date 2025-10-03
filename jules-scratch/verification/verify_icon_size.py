from playwright.sync_api import sync_playwright, expect
import os
import re

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Handle any alert dialogs that might appear
    page.on("dialog", lambda dialog: dialog.dismiss())

    # Get the absolute path to the index.html file
    file_path = os.path.abspath("index.html")

    # Navigate to the local HTML file
    page.goto(f"file://{file_path}")

    # Bypass the API key modal
    page.evaluate("localStorage.setItem('geminiApiKey', 'test_key')")
    page.reload()
    expect(page.locator("#api-modal-overlay")).to_be_hidden()

    # --- Step 1: Generate an article to reveal the prompt generator ---
    page.locator("#topic").fill("Manfaat Teh Hijau")
    page.locator("#keywords").fill("teh hijau, kesehatan")
    # Simulate article generation to show the output and prompt generator
    page.locator("#article-output").evaluate("element => element.innerHTML = '<h1>Manfaat Teh Hijau</h1><p>Ini adalah artikel tentang teh hijau.</p>'")
    page.locator("#output-container").evaluate("element => element.style.display = 'block'")
    page.locator("#image-generator-container").evaluate("element => element.classList.remove('hidden')")

    # --- Step 2: Interact with the Prompt Generator ---
    # Generate a prompt based on the topic
    page.locator("#generate-prompt-btn").click()
    expect(page.locator("#prompt-text")).to_have_value('Sebuah gambar ilustrasi untuk artikel tentang "Manfaat Teh Hijau". Fokus pada kata kunci: teh hijau, kesehatan.')

    # Change aspect ratio
    page.locator('button[data-ratio="16:9"]').click()

    # Convert to JSON
    page.locator("#to-json-btn").click()
    # Use to_have_value with a regex to check the content of the textarea
    expect(page.locator("#prompt-json")).to_have_value(re.compile(r'"aspect_ratio": "16:9"'))

    # --- Step 3: Take a final screenshot for verification ---
    # We'll screenshot the whole container for the generator tab
    page.locator("#content-generator").screenshot(path="jules-scratch/verification/final-verification.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)