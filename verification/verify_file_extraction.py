import os
import time
from playwright.sync_api import sync_playwright

def verify_file_extraction():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context()
        page = context.new_page()

        # Load the file
        file_path = os.path.abspath("index.html")

        page.add_init_script("""
            localStorage.setItem('geminiApiKey', 'dummy-key');
        """)

        page.goto(f"file://{file_path}")

        # Mock the Gemini API call
        page.route("**/generateContent?key=**", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"candidates": [{"content": {"parts": [{"text": "Mock Topic: Success"}]}}]}'
        ))

        # Create a dummy PDF file if it doesn't exist
        with open("test_doc.pdf", "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT /F1 24 Tf 100 700 Td (Hello World form PDF) Tj ET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000257 00000 n \n0000000344 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n439\n%%EOF")

        # 1. Upload a dummy PDF
        pdf_path = os.path.abspath("test_doc.pdf")
        page.set_input_files("#file_upload", pdf_path)

        print("Clicking Generate Ideas button...")

        # Use expect_request context manager
        with page.expect_request(lambda req: "generateContent" in req.url, timeout=10000) as request_info:
            page.click("#generate-ideas-btn")

        request = request_info.value
        post_data = request.post_data_json

        # Inspect the prompt text sent to the AI
        prompt_text = post_data['contents'][0]['parts'][0]['text']
        print("\n--- Prompt Sent to AI ---")
        print(prompt_text[:500] + "..." if len(prompt_text) > 500 else prompt_text)
        print("-------------------------\n")

        if "Hello World form PDF" in prompt_text:
            print("PASS: PDF content 'Hello World form PDF' found in the prompt.")
        else:
            print("FAIL: PDF content not found in the prompt.")

        page.screenshot(path="verification/verification.png")
        browser.close()

if __name__ == "__main__":
    verify_file_extraction()
