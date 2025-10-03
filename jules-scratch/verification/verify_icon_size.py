from playwright.sync_api import sync_playwright, expect
import os

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Handle the alert that will pop up after saving.
    page.on("dialog", lambda dialog: dialog.dismiss())

    # Get the absolute path to the index.html file
    file_path = os.path.abspath("index.html")

    # Navigate to the local HTML file
    page.goto(f"file://{file_path}")

    # The API key modal might appear. We can bypass it by setting the key in localStorage
    # and then reloading the page.
    page.evaluate("localStorage.setItem('geminiApiKey', 'test_key')")

    # A reload will ensure the DOMContentLoaded logic runs again with the key present.
    page.reload()

    # The modal should not be visible now.
    expect(page.locator("#api-modal-overlay")).to_be_hidden()

    # Take a screenshot of the main generator content area
    generator_content = page.locator("#content-generator")
    generator_content.screenshot(path="jules-scratch/verification/verification-all-changes.png")

    # Now, let's create and save an article to make the DB section appear.
    page.locator("#article-output").evaluate("element => element.innerHTML = '<h1>My Test Article</h1><p>Hello world</p>'")
    page.locator("#output-container").evaluate("element => element.style.display = 'block'")
    page.locator("#save-btn").click()

    article_db_container = page.locator("#article-db-container")
    expect(article_db_container).to_be_visible()

    # Take a screenshot of the article database section to verify icon fix
    article_db_container.screenshot(path="jules-scratch/verification/verification-icon-fix.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)