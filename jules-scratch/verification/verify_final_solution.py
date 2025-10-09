import os
import re
import json
from playwright.sync_api import sync_playwright, Page, expect

# Gunakan kunci API asli yang diberikan oleh pengguna untuk pengujian end-to-end
REAL_RAPID_API_KEY = "de052a4cebmshc752ecabb485174p16abefjsn73afeaf7509f"

def setup_page(page: Page):
    """Mempersiapkan halaman dengan mengatur kunci API di localStorage."""
    absolute_path = os.path.abspath('index.html')
    page.goto(f"file://{absolute_path}")
    page.evaluate(f"""
        localStorage.setItem('geminiApiKey', 'DUMMY_GEMINI_KEY_FOR_TEST');
        localStorage.setItem('rapidApiKey', '{REAL_RAPID_API_KEY}');
    """)
    page.goto(f"file://{absolute_path}")
    expect(page.locator("#api-modal-overlay")).to_be_hidden()
    print("Setup: Halaman siap dengan Kunci API yang dikonfigurasi.")

def run_test(page: Page):
    setup_page(page)

    # --- Skenario 1: Gagal (Video tanpa transkrip) ---
    print("\nMemulai Skenario 1: Pengujian Penanganan Error 'Transkrip Tidak Tersedia'")

    failing_youtube_url = "https://www.youtube.com/watch?v=b5ia6KH0lg4"
    youtube_input = page.locator('input[name="url_youtube"]').first
    generate_ideas_btn = page.locator('#generate-ideas-btn')
    error_div = page.locator('#youtube-transcript-error')

    # Pastikan error div tersembunyi pada awalnya
    expect(error_div).to_be_hidden()

    # Masukkan URL yang gagal dan klik generate
    youtube_input.fill(failing_youtube_url)
    generate_ideas_btn.click()

    # Verifikasi bahwa pesan error yang benar muncul
    expect(error_div).to_be_visible(timeout=20000)
    expect(error_div).to_contain_text("Transkrip tidak tersedia untuk video ini", timeout=5000)
    print("Verifikasi Skenario 1 Berhasil: Pesan error 'Transkrip tidak tersedia' ditampilkan dengan benar.")

    # Ambil screenshot untuk bukti
    page.screenshot(path="jules-scratch/verification/verification_failure_scenario.png")
    print("Screenshot skenario kegagalan berhasil diambil.")

    # --- Skenario 2: Sukses (Video dengan transkrip) ---
    print("\nMemulai Skenario 2: Pengujian Alur Sukses")

    # Hapus input lama dan pastikan error hilang
    youtube_input.fill("")
    topic_input = page.locator('#topic')
    topic_input.fill("Topik Tes") # Mengisi topik untuk memicu pembersihan error
    generate_ideas_btn.click()
    expect(error_div).to_be_hidden(timeout=10000)
    print("Pembersihan: Pesan error berhasil disembunyikan pada permintaan baru.")

    # Hapus topik untuk pengujian baru
    topic_input.fill("")

    # Gunakan video yang dijamin punya transkrip
    success_youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Video Rick Astley
    youtube_input.fill(success_youtube_url)

    # Mock panggilan ke Gemini agar tidak menggunakan kuota AI asli untuk pengujian
    def capture_gemini_request(route):
        payload = route.request.post_data_json
        print("Menangkap payload yang dikirim ke Gemini...")
        # Periksa apakah transkrip ada di dalam payload
        assert "Rick Astley" in payload['contents'][0]['parts'][0]['text'], "Transkrip tidak ditemukan di dalam payload Gemini."
        print("Verifikasi Payload Berhasil: Transkrip terkirim ke Gemini.")

        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "candidates": [{"content": {"parts": [{"text": "Topik Relevan Berdasarkan Lagu"}]}}]
            })
        )

    page.route(re.compile(".*generativelanguage.googleapis.com.*"), capture_gemini_request)

    # Klik generate
    generate_ideas_btn.click()

    # Verifikasi hasilnya
    expect(topic_input).to_have_value("Topik Relevan Berdasarkan Lagu", timeout=20000)
    expect(error_div).to_be_hidden()
    print("Verifikasi Skenario 2 Berhasil: Topik relevan berhasil dibuat tanpa error.")

    # Ambil screenshot akhir
    page.screenshot(path="jules-scratch/verification/verification_success_scenario.png")
    print("Screenshot skenario sukses berhasil diambil.")
    print("\nSemua skenario verifikasi final telah berhasil!")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            run_test(page)
        except Exception as e:
            print(f"Terjadi error saat verifikasi: {e}")
            page.screenshot(path="jules-scratch/verification/error_script_final.png")
        finally:
            browser.close()

if __name__ == "__main__":
    main()