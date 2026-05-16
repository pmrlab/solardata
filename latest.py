from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import time

# =========================
# FOLDERS
# =========================
BASE_DIR = os.path.abspath("isolar_data")

FOLDERS = {
    "overview": os.path.join(BASE_DIR, "overview"),
    "miic1": os.path.join(BASE_DIR, "miic1"),
    "miic2": os.path.join(BASE_DIR, "miic2"),
}

for f in FOLDERS.values():
    os.makedirs(f, exist_ok=True)

# =========================
# DOWNLOAD HELPER (2-STEP)
# =========================
def download_csv(page, folder, prefix):
    # open export menu
    page.locator(".icon-G2_Download_24").first.click()
    page.wait_for_timeout(1000)

    # real download trigger
    with page.expect_download(timeout=30000) as d:
        page.get_by_text("Export as CSV").click()

    download = d.value
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    download.save_as(os.path.join(folder, filename))
    print(f"Downloaded → {filename}")

    # close export overlay
    page.keyboard.press("Escape")
    page.wait_for_timeout(1500)

# =========================
# MAIN
# =========================
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
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
    # OVERVIEW
    # =========================
    print("Downloading OVERVIEW...")
    download_csv(page, FOLDERS["overview"], "overview")
    # CURVE → DOWNLOAD
    # =========================
      # =========================
    # CURVE → DOWNLOAD
    # =========================
    page.get_by_text("Curve").first.click()
    page.wait_for_timeout(2000)
    '''download_csv(page, FOLDERS["curve"], "curve")
    page.wait_for_timeout(3000)'''

    # =========================
    # MIIC 1 → DOWNLOAD
    # =========================
    page.get_by_role("img").nth(2).click()
    page.get_by_text("MIIC 1").click()
    page.wait_for_timeout(2000)
    download_csv(page, FOLDERS["miic1"], "miic1")
    page.wait_for_timeout(3000)

    # =========================
    # MIIC 2 → DOWNLOAD
    # =========================
    page.get_by_role("img").nth(2).click()
    page.get_by_text("MIIC 2").click()
    page.wait_for_timeout(2000)
    download_csv(page, FOLDERS["miic2"], "miic2")

    print("✅ All downloads completed")
    browser.close()
