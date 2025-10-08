import pytest
from playwright.sync_api import sync_playwright, Page, expect
import os
import re

# --- Test Setup ---
@pytest.fixture(scope="function") # Use function scope for test isolation
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Get absolute path for local file
        file_path = os.path.abspath('index.html')
        page.goto(f"file://{file_path}")

        # Set a dummy API key in localStorage to prevent the modal from appearing
        page.evaluate("() => { localStorage.setItem('geminiApiKey', 'DUMMY_KEY'); }")
        # Reload the page for the key to be recognized
        page.reload()

        # Set up the editor for testing
        setup_editor_with_content(page)

        yield page
        browser.close()

def setup_editor_with_content(page: Page):
    """Prepares the editor by manually displaying it and making it editable, bypassing the AI call."""
    # Manually make the output container and editor controls visible
    page.evaluate("""() => {
        document.getElementById('output-container').style.display = 'block';
        const editorControls = document.getElementById('editor-controls');
        editorControls.classList.remove('hidden');
        editorControls.classList.add('flex');
    }""")

    article_output = page.locator("#article-output")

    # Click the 'Edit' button to enable the contentEditable property and the toolbar
    page.get_by_role("button", name="Edit Artikel").click()

    # Verify the editor is now editable
    expect(article_output).to_be_editable()

    # Set initial content
    article_output.fill("Ini adalah konten awal untuk pengujian. ")

# --- Locators ---
def get_locators(page: Page):
    return {
        "editor": page.locator("#article-output"),
        "insert_image_btn": page.locator("#insert-image-btn"),
        "image_modal": page.locator("#image-modal-overlay"),
        "image_url_input": page.locator("#image-url-input"),
        "image_alt_input": page.locator("#image-alt-text"),
        "confirm_image_btn": page.locator("#confirm-image-btn"),
        "context_menu": page.locator("#image-context-menu"),
        "alt_text_modal": page.locator("#alt-text-modal-overlay"),
        "confirm_alt_text_btn": page.locator("#confirm-alt-text-btn"),
        "alt_text_input": page.locator("#alt-text-input"),
        "delete_image_modal": page.locator("#delete-image-modal-overlay"),
        "confirm_delete_image_btn": page.locator("#confirm-delete-image-btn"),
        "undo_btn": page.locator("button[onclick=\"formatDoc('undo')\"]"),
        "redo_btn": page.locator("button[onclick=\"formatDoc('redo')\"]"),
        "justify_center_btn": page.locator("button[onclick=\"formatDoc('justifyCenter')\"]"),
        "justify_right_btn": page.locator("button[onclick=\"formatDoc('justifyRight')\"]"),
        "justify_left_btn": page.locator("button[onclick=\"formatDoc('justifyLeft')\"]"),
    }

# --- Helper Functions ---
def insert_image(page: Page, url: str, alt: str):
    locators = get_locators(page)
    locators["insert_image_btn"].click()
    expect(locators["image_modal"]).to_be_visible()
    locators["image_url_input"].fill(url)
    locators["image_alt_input"].fill(alt)
    locators["confirm_image_btn"].click()
    expect(locators["image_modal"]).to_be_hidden()

def select_image(page: Page, img_locator):
    img_locator.click()
    # After clicking, the image should have the temp ID and its wrapper the 'selected' class
    wrapper = page.locator(f'div.resize-wrapper:has(img#image-being-edited)')
    expect(wrapper).to_have_class(re.compile(r"\bselected\b"))
    expect(wrapper).to_be_visible()
    return wrapper

# --- Test Cases ---

def test_image_insertion_and_selection(page: Page):
    """Verify that an image can be inserted and selected, showing handles and context menu."""
    locators = get_locators(page)
    editor = locators["editor"]

    # 1. Insert an image
    image_url = "https://via.placeholder.com/150"
    image_alt = "Placeholder Image"
    insert_image(page, image_url, image_alt)

    # 2. Verify image exists in the editor
    img_locator = editor.locator(f'img[alt="{image_alt}"]')
    expect(img_locator).to_have_count(1)
    expect(img_locator).to_have_attribute("src", image_url)

    # 3. Verify selection
    wrapper = select_image(page, img_locator)
    expect(wrapper.locator(".resize-handle")).to_have_count(4)
    expect(locators["context_menu"]).to_be_visible()

    # 4. Verify deselection
    editor.click(position={"x": 5, "y": 5}) # Click somewhere else in the editor
    expect(page.locator(".resize-wrapper.selected")).to_have_count(0)
    expect(locators["context_menu"]).to_be_hidden()

    # Cleanup is handled by the function-scoped fixture, no need for manual deletion

def test_context_menu_actions(page: Page):
    """Verify all actions in the context menu: edit alt, link, and delete."""
    locators = get_locators(page)
    editor = locators["editor"]

    # --- Setup ---
    image_url = "https://via.placeholder.com/150/0000FF/808080?text=Test"
    initial_alt = "Initial Alt Text"
    insert_image(page, image_url, initial_alt)
    img_locator = editor.locator(f'img[alt="{initial_alt}"]')
    select_image(page, img_locator)

    # --- 1. Edit Alt Text ---
    locators["context_menu"].get_by_role("button", name="Edit Alt Text").click()
    expect(locators["alt_text_modal"]).to_be_visible()
    new_alt = "Updated Alt Text"
    locators["alt_text_input"].fill(new_alt)
    locators["confirm_alt_text_btn"].click()
    expect(locators["alt_text_modal"]).to_be_hidden()

    # Verify the alt text was updated.
    updated_img_locator = editor.locator(f'img[alt="{new_alt}"]')
    expect(updated_img_locator).to_have_count(1)

    # --- 2. Insert Link ---
    select_image(page, updated_img_locator) # Reselect the image with the new alt text
    page.once("dialog", lambda dialog: dialog.accept(prompt_text="https://example.com"))
    locators["context_menu"].get_by_role("button", name="Sisipkan Link").click()

    # Verify link is created
    link_locator = editor.locator('a[href="https://example.com"]')
    expect(link_locator).to_have_count(1, timeout=2000)
    expect(link_locator.locator(f'img[alt="{new_alt}"]')).to_have_count(1)

    # --- 3. Delete Image ---
    select_image(page, updated_img_locator) # Reselect
    locators["context_menu"].get_by_role("button", name="Hapus Gambar").click()

    delete_modal = locators["delete_image_modal"]
    expect(delete_modal).to_be_visible()
    delete_modal.get_by_role("button", name="Hapus").click()

    expect(delete_modal).to_be_hidden()
    expect(updated_img_locator).to_have_count(0)

def test_image_resizing(page: Page):
    """Verify that dragging a resize handle changes the image's width."""
    locators = get_locators(page)
    editor = locators["editor"]

    # --- Setup ---
    insert_image(page, "https://via.placeholder.com/100", "Resizable")
    img_locator = editor.locator('img[alt="Resizable"]')
    wrapper = select_image(page, img_locator)

    initial_width = img_locator.bounding_box()["width"]

    # --- Drag the bottom-right handle ---
    handle = wrapper.locator(".resize-handle.bottom-right")
    handle_box = handle.bounding_box()

    start_x = handle_box["x"] + handle_box["width"] / 2
    start_y = handle_box["y"] + handle_box["height"] / 2

    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(start_x + 50, start_y + 50) # Corrected drag destination
    page.mouse.up()

    final_width = img_locator.bounding_box()["width"]

    # --- Verify ---
    assert final_width > initial_width + 40

def test_image_alignment(page: Page):
    """Verify image alignment using toolbar buttons."""
    locators = get_locators(page)
    editor = locators["editor"]

    # --- Setup ---
    insert_image(page, "https://via.placeholder.com/100", "Align Me")
    img_locator = editor.locator('img[alt="Align Me"]')
    select_image(page, img_locator)

    # The parent <p> tag is what gets alignment styles.
    parent_paragraph = editor.locator('p:has(img[alt="Align Me"])')

    # --- 1. Center Align ---
    locators["justify_center_btn"].click()
    expect(parent_paragraph).to_have_attribute("style", "text-align: center;")

    # --- 2. Right Align ---
    locators["justify_right_btn"].click()
    expect(parent_paragraph).to_have_attribute("style", "text-align: right;")

    # --- 3. Left Align ---
    locators["justify_left_btn"].click()
    expect(parent_paragraph).to_have_attribute("style", "text-align: left;")

def test_delete_with_keyboard(page: Page):
    """Verify that pressing Delete or Backspace removes the selected image."""
    locators = get_locators(page)
    editor = locators["editor"]

    # --- Setup ---
    insert_image(page, "https://via.placeholder.com/100", "Deletable")
    img_locator = editor.locator('img[alt="Deletable"]')
    select_image(page, img_locator)

    # --- Delete with 'Delete' key ---
    page.keyboard.press("Delete")

    # --- Verify ---
    delete_modal = locators["delete_image_modal"]
    expect(delete_modal).to_be_visible()
    delete_modal.get_by_role("button", name="Hapus").click()
    expect(img_locator).to_have_count(0)

    # --- Test with 'Backspace' key ---
    insert_image(page, "https://via.placeholder.com/100", "Deletable2")
    img_locator2 = editor.locator('img[alt="Deletable2"]')
    select_image(page, img_locator2)
    page.keyboard.press("Backspace")

    # --- Verify ---
    expect(delete_modal).to_be_visible()
    delete_modal.get_by_role("button", name="Hapus").click()
    expect(img_locator2).to_have_count(0)

def test_linked_image_can_be_reselected_and_edited(page: Page):
    """Verify that an image with a link can be selected again without navigation."""
    locators = get_locators(page)
    editor = locators["editor"]

    # --- Setup: Insert and link an image ---
    initial_alt = "Linked Image"
    insert_image(page, "https://via.placeholder.com/100", initial_alt)
    img_locator = editor.locator(f'img[alt="{initial_alt}"]')
    select_image(page, img_locator)

    page.once("dialog", lambda dialog: dialog.accept(prompt_text="https://example.com"))
    locators["context_menu"].get_by_role("button", name="Sisipkan Link").click()
    link_locator = editor.locator('a[href="https://example.com"]')
    expect(link_locator).to_be_visible(timeout=2000)

    # Deselect by clicking away.
    editor.click(position={"x": 5, "y": 5})
    expect(locators["context_menu"]).to_be_hidden()
    expect(page.locator(".resize-wrapper.selected")).to_have_count(0)

    # --- Test: Reselect the linked image ---
    img_locator.click()

    # --- Verify ---
    wrapper = page.locator(f'div.resize-wrapper:has(img[alt="{initial_alt}"])')
    expect(wrapper).to_have_class(re.compile(r"\bselected\b"))
    expect(locators["context_menu"]).to_be_visible()

    # Verify we can still perform an action.
    locators["context_menu"].get_by_role("button", name="Edit Alt Text").click()
    expect(locators["alt_text_modal"]).to_be_visible()
    new_alt = "New Alt for Linked Image"
    locators["alt_text_input"].fill(new_alt)
    locators["confirm_alt_text_btn"].click()

    img_after_edit_locator = editor.locator(f'img[alt="{new_alt}"]')
    expect(img_after_edit_locator).to_have_count(1)