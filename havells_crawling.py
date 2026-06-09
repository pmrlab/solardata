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
    
    # 🔥 FIXED: Correct Python syntax for force-clicking
    locator.click(force=True)

    page.wait_for_timeout(3000)

    with page.expect_download() as d:
        page.get_by_role("button", name="Export").click()

    download = d.value

    # Delete any old file for this plant before saving new one
    folder_path = os.path.join(BASE_DIR, folder_name)
    for fname in os.listdir(folder_path):
        if fname.startswith(folder_name) and fname.endswith(".xlsx"):
            try:
                os.remove(os.path.join(folder_path, fname))
                print(f"  🗑️  Deleted old: {fname}")
            except: pass

    filename = f"{folder_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    path = os.path.join(BASE_DIR, folder_name, filename)
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