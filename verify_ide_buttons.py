
import os
import time
from playwright.sync_api import sync_playwright

def verify_ide_buttons():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context()
        page = context.new_page()

        file_path = os.path.abspath("index.html")
        page.add_init_script("""
            localStorage.setItem('geminiApiKey', 'dummy-key');
        """)

        page.goto(f"file://{file_path}")

        # Mock the Gemini API call
        page.route("**/generateContent?key=**", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"candidates": [{"content": {"parts": [{"text": "- Mock Idea 1\\n- Mock Idea 2"}]}}]}'
        ))

        # Setup dummy content
        page.fill('textarea[name="text_paste"]', "Dummy pasted text content.")

        print("Testing 'Generate Ide' for Text...")
        # Locate the button for text paste section specifically
        # The button is next to the label 'Tempel Teks'
        # We can find it by title attribute

        with page.expect_request(lambda req: "generateContent" in req.url, timeout=10000) as request_info:
            page.click('button[title="Generate Ide dari Teks"]')

        request = request_info.value
        post_data = request.post_data_json
        prompt_text = post_data['contents'][0]['parts'][0]['text']

        print("Prompt sent:")
        print(prompt_text[:200])

        if "Dummy pasted text content" in prompt_text:
            print("PASS: Specific Text Generation works.")
        else:
            print("FAIL: Specific Text Generation failed.")

        # Now test global generation (should include the text)
        print("Testing Global 'GENERATE IDE'...")
        with page.expect_request(lambda req: "generateContent" in req.url, timeout=10000) as request_info:
            page.click('#generate-ideas-btn') # The top button

        request = request_info.value
        post_data = request.post_data_json
        prompt_text = post_data['contents'][0]['parts'][0]['text']

        print("Global Prompt sent:")
        print(prompt_text[:200])

        if "Dummy pasted text content" in prompt_text:
            print("PASS: Global Generation includes text.")
        else:
            print("FAIL: Global Generation missing text.")

        browser.close()

if __name__ == "__main__":
    verify_ide_buttons()
