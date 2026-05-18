from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import time

# =========================
# FOLDERS
# =========================
BASE_DIR = os.path.abspath("isolar_data")

FOLDERS = {
    "Electronic 1": os.path.join(BASE_DIR, "Electronic 1"),
    "Electronic 2": os.path.join(BASE_DIR, "Electronic 2"),
    "miic1": os.path.join(BASE_DIR, "miic1"),
    "miic2": os.path.join(BASE_DIR, "miic2"),
    "Multipath 1": os.path.join(BASE_DIR, "Multipath 1"),
    "Multipath 2": os.path.join(BASE_DIR, "Multipath 2"),
    "Multipath 3": os.path.join(BASE_DIR, "Multipath 3"),
    "Multipath 4": os.path.join(BASE_DIR, "Multipath 4"),
    "Multipath 5": os.path.join(BASE_DIR, "Multipath 5"),
    "Prabha 01": os.path.join(BASE_DIR, "Prabha 01"),
    "Prabha 02": os.path.join(BASE_DIR, "Prabha 02"),
    "VLTC 1": os.path.join(BASE_DIR, "VLTC 1"),
    "VLTC 2": os.path.join(BASE_DIR, "VLTC 2"),
    "VLTC 3": os.path.join(BASE_DIR, "VLTC 3"),
}

for f in FOLDERS.values():
    os.makedirs(f, exist_ok=True)

# =========================
# DOWNLOAD HELPER (UPDATED)
# =========================
def download_csv(page, folder, prefix):
    with page.expect_download() as d:
        page.locator(".icon-G2_Download_24").click()

    download = d.value

    # 🔥 ONLY DATE (overwrite same day)
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d')}.csv"
    path = os.path.join(folder, filename)

    # 🔥 remove old file if exists
    if os.path.exists(path):
        os.remove(path)

    download.save_as(path)
    print(f"✅ Updated (overwritten): {path}")

# =========================
# MAIN
# =========================
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()

    # 1️⃣ LOGIN
    page.goto("https://web3.isolarcloud.com.hk/#/login")
    page.get_by_role("textbox", name="Account").fill("nkjangir.estate@mnit.ac.in")
    page.get_by_role("textbox", name="Password").fill("1234@Asdf")
    page.get_by_role("button", name="Login").click()

    page.wait_for_timeout(8000)

    # 2️⃣ SELECT PLANT
    page.get_by_role("link", name="MNIT Jaipur Guest").click()
    page.wait_for_timeout(5000)

    # 3️⃣ SCROLL
    page.mouse.wheel(0, 3000)
    page.wait_for_timeout(2000)

    # =========================
    # OPEN CURVE SECTION
    # =========================
    page.get_by_text("Curve").first.click()
    page.wait_for_timeout(2000)

    # =========================
    # DOWNLOAD SEQUENCE
    # =========================
    plant_order = [
        "Electronic 1",
        "Electronic 2",
        "MIIC 1",
        "MIIC 2",
        "Multipath 1",
        "Multipath 2",
        "Multipath 3",
        "Multipath 4",
        "Multipath 5"
    ]

    for plant in plant_order:
        page.get_by_role("img").nth(2).click()
        page.get_by_text(plant).click()
        page.wait_for_timeout(2000)

        if plant in FOLDERS:
            download_csv(page, FOLDERS[plant], plant)
        else:
            if plant == "MIIC 1":
                download_csv(page, FOLDERS["miic1"], "miic1")
            elif plant == "MIIC 2":
                download_csv(page, FOLDERS["miic2"], "miic2")

        page.wait_for_timeout(3000)

    # =========================
    # SCROLL DOWN
    # =========================
    page.mouse.wheel(0, 3000)
    page.wait_for_timeout(2000)

    # =========================
    # PRABHA DOWNLOAD
    # =========================
    for plant in ["Prabha 01", "Prabha 02", "VLTC 1", "VLTC 2", "VLTC 3"]:
        page.get_by_role("img").nth(2).click()
        page.get_by_text(plant).click()
        page.wait_for_timeout(2000)

        download_csv(page, FOLDERS[plant], plant)
        page.wait_for_timeout(3000)

    print("🎉 All downloads updated (no duplicates)")
    browser.close()