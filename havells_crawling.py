from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import time

# =========================
# FOLDER SETUP
# =========================
BASE_DIR = os.path.abspath("havells_data")

PLANTS = {
    "Computer Deptt SJ2ES350N98002": "computer_dept",
    "Prabha Bhawan Inv 2": "prabha_2",
    "Prabha Bhawan Inv 1": "prabha_1",
    "Prabha Bhawan Inv 3": "prabha_3",
    "Electrical Depatt": "electrical",
    "Metallurgical Dep.": "metallurgical"
}

# Create folders
for folder in PLANTS.values():
    os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

# =========================
# DOWNLOAD FUNCTION (UPDATED)
# =========================
def download_file(page, plant_name, folder_name):
    print(f"➡️ Processing: {plant_name}")

    locator = page.get_by_text(plant_name)
    locator.scroll_into_view_if_needed()
    locator.click()

    page.wait_for_timeout(3000)

    with page.expect_download() as d:
        page.get_by_role("button", name="Export").click()

    download = d.value

    # 🔥 ONLY DATE (NO TIME → overwrite same file)
    filename = f"{folder_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    path = os.path.join(BASE_DIR, folder_name, filename)

    # 🔥 Overwrite existing file
    if os.path.exists(path):
        os.remove(path)

    download.save_as(path)
    print(f"✅ Updated (overwritten): {path}")

    # Close popup
    try:
        page.locator(".close-btn").click()
    except:
        pass

    page.wait_for_timeout(2000)

# =========================
# MAIN SCRIPT
# =========================
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        storage_state="session.json",
        accept_downloads=True,
        ignore_https_errors=True
    )

    page = context.new_page()

    page.goto("https://pvcheck.havells.com/plant/infos/device")
    page.wait_for_timeout(8000)

    print("✅ Logged in via saved session")

    page.mouse.wheel(0, 3000)
    time.sleep(2)

    for plant, folder in PLANTS.items():
        try:
            download_file(page, plant, folder)
        except Exception as e:
            print(f"❌ Error with {plant}: {e}")

    print("🎉 All downloads completed")
    browser.close()