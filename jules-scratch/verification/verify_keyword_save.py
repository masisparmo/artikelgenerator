import asyncio
from playwright.sync_api import sync_playwright, expect
import os

def run_verification(page):
    # Navigate to the page served by the local HTTP server
    page.goto('http://localhost:8080/index.html')

    # --- Handle API Key Modal ---
    # The modal should appear on first load. We'll fill it out to proceed.
    api_key_input = page.locator('#api-key-input')
    expect(api_key_input).to_be_visible()
    api_key_input.fill('dummy-api-key')
    page.locator('#save-api-key').click()
    # Wait for the modal to disappear
    expect(page.locator('#api-modal-overlay')).to_be_hidden()


    # --- Test Logic ---
    # 1. Inject a sample article with initial keywords into IndexedDB
    article_to_add = {
        "id": 1, # Explicitly set an ID for predictability
        "title": "Test Article for Keywords",
        "content": "<h1>Test Article for Keywords</h1><p>This is the content.</p>",
        "keywords": "initial, keywords, test"
    }

    # This JS code opens the DB and adds the article
    page.evaluate("""
        (async (article) => {
            return new Promise((resolve, reject) => {
                const request = indexedDB.open("ArticleGeneratorDB", 1);
                request.onsuccess = (event) => {
                    const db = event.target.result;
                    // Ensure object store exists before transaction
                    if (!db.objectStoreNames.contains('articles')) {
                        db.close();
                        const upgradeReq = indexedDB.open("ArticleGeneratorDB", 2);
                        upgradeReq.onupgradeneeded = (e) => {
                            e.target.result.createObjectStore("articles", { keyPath: "id", autoIncrement: true });
                        };
                        upgradeReq.onsuccess = (e) => {
                             const db2 = e.target.result;
                             const transaction = db2.transaction(["articles"], "readwrite");
                             const objectStore = transaction.objectStore("articles");
                             const addRequest = objectStore.put(article); // Use put to handle re-runs
                             addRequest.onsuccess = () => resolve();
                             addRequest.onerror = (e) => reject("Failed to add article: " + e.target.errorCode);
                        }
                        return;
                    }
                    const transaction = db.transaction(["articles"], "readwrite");
                    const objectStore = transaction.objectStore("articles");
                    const addRequest = objectStore.put(article); // Use put to handle re-runs
                    addRequest.onsuccess = () => resolve();
                    addRequest.onerror = (e) => reject("Failed to add article: " + e.target.errorCode);
                };
                request.onerror = (e) => reject("Failed to open DB: " + e.target.errorCode);
            });
        })
    """, article_to_add)

    # 2. Reload the page to see the new article in the list
    page.reload()

    # Wait for the article list to be populated and the API modal to be gone
    expect(page.locator('#api-modal-overlay')).to_be_hidden()
    page.wait_for_selector('#article-list div')

    # 3. Find the new article and click its edit button
    article_entry = page.locator('div.flex:has-text("Test Article for Keywords")')
    edit_button = article_entry.locator('svg[data-action="edit"]')
    edit_button.click()

    # 4. Verify initial keywords are loaded, then update them
    keywords_input = page.locator('#keywords')
    expect(keywords_input).to_have_value("initial, keywords, test")

    updated_keywords = "updated, keywords, verified"
    keywords_input.fill(updated_keywords)

    # 5. Save the article
    # We need to handle the alert dialog that pops up
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator('#save-btn').click()

    # Wait for the confirmation alert to be handled.
    page.wait_for_timeout(500) # Give DB time to update

    # 6. Load the article again to check if keywords were saved
    page.reload()
    page.wait_for_selector('#article-list div')
    article_entry = page.locator('div.flex:has-text("Test Article for Keywords")')
    edit_button = article_entry.locator('svg[data-action="edit"]')
    edit_button.click()

    # 7. Assert that the keywords are the updated ones
    expect(keywords_input).to_have_value(updated_keywords)

    # 8. Take a screenshot for visual confirmation
    screenshot_path = 'jules-scratch/verification/verification.png'
    page.screenshot(path=screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Set a higher timeout for DB operations
        page.set_default_timeout(10000)
        run_verification(page)
        browser.close()

if __name__ == "__main__":
    main()