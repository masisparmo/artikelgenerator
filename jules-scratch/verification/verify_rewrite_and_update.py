import asyncio
from playwright.sync_api import sync_playwright, expect
import os

def run_verification(page):
    # Navigate to the page served by the local HTTP server
    page.goto('http://localhost:8080/index.html')

    # --- Clear IndexedDB to ensure a clean state ---
    page.evaluate("""async () => {
        return new Promise((resolve, reject) => {
            const deleteRequest = indexedDB.deleteDatabase('ArticleGeneratorDB');
            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = (e) => reject('Failed to delete DB: ' + e.target.errorCode);
            // onblocked can happen if the page has an open connection. Reloading should fix this.
            deleteRequest.onblocked = () => {
                console.warn('Database deletion blocked. The test will proceed, but this might indicate an issue.');
                resolve();
            };
        });
    }""")
    # Reload the page to ensure the app re-initializes its DB connection from a clean state
    page.reload()

    # --- Handle API Key Modal ---
    api_key_input = page.locator('#api-key-input')
    expect(api_key_input).to_be_visible()
    api_key_input.fill('dummy-api-key')
    page.locator('#save-api-key').click()
    expect(page.locator('#api-modal-overlay')).to_be_hidden()

    # --- Test Logic ---
    # 1. Create and save an initial article
    page.locator('#topic').fill("Original Article")
    page.locator('#keywords').fill("original, keyword")

    # Mock the AI response for creating the initial article
    page.route("**/models/gemini-1.5-flash:generateContent**", lambda route: route.fulfill(
        status=200,
        headers={"Content-Type": "application/json"},
        body='{"candidates": [{"content": {"parts": [{"text": "# Original Article\\nThis is the original content."}]}}]}'
    ))

    page.once("dialog", lambda dialog: dialog.accept()) # Accept the "saved" alert
    page.locator('#generate-btn').click()
    page.locator('#save-btn').click()

    # Wait for the article list to show one item
    expect(page.locator('#article-list div')).to_have_count(1)

    # 2. Rewrite the article
    # Mock the AI response for the rewrite
    page.unroute("**/models/gemini-1.5-flash:generateContent**")
    page.route("**/models/gemini-1.5-flash:generateContent**", lambda route: route.fulfill(
        status=200,
        headers={"Content-Type": "application/json"},
        body='{"candidates": [{"content": {"parts": [{"text": "# Rewritten Article\\nThis is the rewritten content."}]}}]}'
    ))

    page.locator('#rewrite-btn').click()
    page.locator('#confirm-rewrite-btn').click()

    # Wait for the rewritten content to appear
    expect(page.locator('#article-output h1')).to_have_text("Rewritten Article")

    # 3. Save the rewritten article (should be a NEW entry)
    page.once("dialog", lambda dialog: dialog.accept()) # Accept the "new article saved" alert
    page.locator('#save-btn').click()

    # Wait for the article list to show two items
    expect(page.locator('#article-list div')).to_have_count(2)
    expect(page.locator('div.flex:has-text("Rewritten Article")')).to_be_visible()

    # 4. Load the ORIGINAL article again
    page.locator('div.flex:has-text("Original Article")').locator('svg[data-action="edit"]').click()
    expect(page.locator('#article-output h1')).to_have_text("Original Article")

    # 5. Modify its keywords and save (should be an UPDATE)
    keywords_input = page.locator('#keywords')
    expect(keywords_input).to_have_value("original, keyword")
    keywords_input.fill("original, keyword, updated")

    page.once("dialog", lambda dialog: dialog.accept()) # Accept the "updated" alert
    page.locator('#save-btn').click()
    page.wait_for_timeout(500) # Give UI time to process

    # 6. Verify that there are still only two articles
    expect(page.locator('#article-list div')).to_have_count(2)

    # 7. Final verification by loading the updated original article
    page.locator('div.flex:has-text("Original Article")').locator('svg[data-action="edit"]').click()
    expect(page.locator('#keywords')).to_have_value("original, keyword, updated")

    # 8. Take a screenshot for visual confirmation
    screenshot_path = 'jules-scratch/verification/verification_rewrite.png'
    page.screenshot(path=screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(15000)
        run_verification(page)
        browser.close()

if __name__ == "__main__":
    main()