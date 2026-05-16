from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://pvcheck.havells.com")

    print("👉 Login manually and solve CAPTCHA...")
    input("Press ENTER after login is successful...")

    context.storage_state(path="auth.json")
    print("✅ Session saved!")