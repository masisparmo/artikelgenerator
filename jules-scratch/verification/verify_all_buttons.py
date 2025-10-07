import os
import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        # Get absolute path for index.html
        file_path = os.path.abspath('index.html')
        await page.goto(f'file://{file_path}')

        # --- SETUP ---
        # 1. Bypass API Key Modal
        await page.evaluate("localStorage.setItem('geminiApiKey', 'DUMMY_KEY')")

        # 2. Add dummy data to IndexedDB
        initial_ideas = ["Test Idea 1: How to bake a cake", "Test Idea 2: Intro to Playwright"]
        await page.evaluate("""(ideas) => {
            return new Promise((resolve, reject) => {
                const request = indexedDB.open('ArticleGeneratorDB', 1);
                request.onsuccess = (event) => {
                    const db = event.target.result;
                    const transaction = db.transaction(['ideas'], 'readwrite');
                    const objectStore = transaction.objectStore('ideas');
                    for (const idea of ideas) {
                        objectStore.add({ idea: idea });
                    }
                    transaction.oncomplete = () => resolve();
                    transaction.onerror = (err) => reject(err);
                };
                request.onerror = (err) => reject(err);
            });
        }""", initial_ideas)

        # 3. Reload the page to display the ideas
        await page.reload()

        # 4. Verify the database container is visible
        idea_db_container = page.locator('#idea-db-container')
        await expect(idea_db_container).to_be_visible()
        await expect(page.locator('.idea-item')).to_have_count(2)
        print("✅ Setup complete: Database populated with 2 ideas.")

        # --- TEST 'USE' BUTTON ---
        first_idea_item = page.locator('.idea-item').first
        use_button = first_idea_item.locator('[data-action="use"]')
        await use_button.click()
        await expect(page.locator('#topic')).to_have_value(initial_ideas[0])
        print("✅ 'Use' button works as expected.")

        # --- TEST 'EDIT' BUTTON ---
        second_idea_item = page.locator('.idea-item').last
        edit_button = second_idea_item.locator('[data-action="edit"]')
        await edit_button.click()

        edit_modal = page.locator('#edit-idea-modal-overlay')
        await expect(edit_modal).to_be_visible()

        edit_textarea = edit_modal.locator('#edit-idea-text')
        await expect(edit_textarea).to_have_value(initial_ideas[1])

        updated_idea_text = "Test Idea 2: Advanced Playwright"
        await edit_textarea.fill(updated_idea_text)
        await edit_modal.locator('#confirm-edit-idea-btn').click()

        await expect(edit_modal).to_be_hidden()
        await expect(second_idea_item.locator('span')).to_have_text(updated_idea_text)
        print("✅ 'Edit' button and modal work as expected.")

        # --- TEST 'DELETE' BUTTON ---
        # Auto-accept the confirmation dialog
        page.on("dialog", lambda dialog: dialog.accept())

        await first_idea_item.locator('[data-action="delete"]').click()

        await expect(page.locator('.idea-item')).to_have_count(1)
        await expect(page.locator('.idea-item').first.locator('span')).to_have_text(updated_idea_text)
        print("✅ 'Delete' button works as expected.")

        # --- FINAL SCREENSHOT ---
        await idea_db_container.screenshot(path='jules-scratch/verification/final_verification.png')
        print("📸 Final state screenshot captured.")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())