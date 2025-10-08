import pytest
import os
import re
from playwright.sync_api import sync_playwright, Page, expect

@pytest.fixture(scope="function")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Dapatkan path absolut ke index.html
        # Diperlukan karena Playwright butuh path lengkap untuk file lokal
        file_path = os.path.abspath('index.html')
        page.goto(f"file://{file_path}")

        # Atasi modal API Key yang muncul pertama kali
        # dengan memasukkan dummy key ke localStorage dan reload
        page.evaluate("localStorage.setItem('geminiApiKey', 'DUMMY_KEY_FOR_TESTING')")
        page.reload()

        yield page
        browser.close()

def test_default_ui_state(page: Page):
    """
    Verifikasi bahwa "Database Artikel" dan Editor Artikel terlihat dan aktif secara default.
    """
    # 1. Verifikasi Database Artikel terlihat
    article_db_container = page.locator("#article-db-container")
    expect(article_db_container).to_be_visible()

    # 2. Verifikasi pesan "kosong" ditampilkan di dalam database artikel
    expect(article_db_container.locator("p")).to_have_text("Database artikel Anda masih kosong.")

    # 3. Verifikasi kontainer output utama terlihat
    output_container = page.locator("#output-container")
    expect(output_container).to_be_visible()

    # 4. Verifikasi toolbar editor terlihat
    editor_controls = page.locator("#editor-controls")
    expect(editor_controls).to_be_visible()

    # 5. Verifikasi area artikel dapat diedit (contenteditable=true)
    article_output = page.locator("#article-output")
    expect(article_output).to_have_attribute("contenteditable", "true")

    # 6. Verifikasi tombol "Selesai" (sebelumnya "Edit Artikel") terlihat
    edit_btn = page.locator("#edit-btn")
    expect(edit_btn).to_be_visible()
    expect(edit_btn).to_have_text("Selesai")

    # 7. Verifikasi tombol "BATAL" terlihat
    cancel_edit_btn = page.locator("#cancel-edit-btn")
    expect(cancel_edit_btn).to_be_visible()

    # 8. Verifikasi Image Prompt Generator terlihat
    image_generator = page.locator("#image-generator-container")
    expect(image_generator).to_be_visible()

    # 9. Ambil screenshot untuk verifikasi visual
    screenshot_path = "default_view_verification.png"
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"\nScreenshot verifikasi disimpan di: {screenshot_path}")