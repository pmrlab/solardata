from playwright.sync_api import sync_playwright
from datetime import datetime
import os

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    # 🔥 USE SAVED SESSION
    context = browser.new_context(
        storage_state="session.json",
        accept_downloads=True
    )

    page = context.new_page()

    # 👉 Go directly to device page
    page.goto("https://pvcheck.havells.com/plant/infos/device")

    page.wait_for_timeout(8000)

    print("✅ Logged in automatically (no captcha)")

    # 🔽 CLICK EXPORT BUTTON
    with page.expect_download() as download_info:
        page.get_by_text("Export").click()

    download = download_info.value

    filename = f"havells_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    path = os.path.join(DOWNLOAD_DIR, filename)

    download.save_as(path)

    print(f"✅ Downloaded: {path}")

    browser.close()