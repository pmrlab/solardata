"""
eWatch scraper — Full Automation
Saves to: ewatch_data/

KEY NOTES:
 - Parameter name on site is 'Abs Active Energy' (matched by 'Abs Active')
 - Shiftwise / Cons-Gen Monthly tab uses month+year <select> dropdowns
 - Meter data export & Target vs actual: Export button is top-right <a> link
 - Export button must be clicked INSIDE expect_download context
 - Target vs actual energy: nav label confirmed from Analysis dropdown
 - Download timeout: 20s then proceed
 - Both locations moved to right together before downloading (listed pages)
 - Saving interval wise: single-select dropdown, one download per area
"""

from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import os, io, time, re
import ddddocr
from PIL import Image

# ─────────────────────────────────────────
# FOLDERS & CONFIG
# ─────────────────────────────────────────
BASE_DIR = os.path.abspath("ewatch_data")
SAVE_DIR = BASE_DIR
os.makedirs(SAVE_DIR, exist_ok=True)

BASE_URL  = "https://dataservices.ewatch.online"
LOGIN_URL = f"{BASE_URL}/pages/CommonPages/application.aspx?login=1"
USERNAME  = "mnitjaipur"
PASSWORD  = "gRHGDd"

MENU_REPORTS  = "Reports"
MENU_ANALYSIS = "Analysis"

ITEM_CONS_GEN   = "Consumption / Generation"
ITEM_SHIFTWISE  = "Shiftwise consumption / generation"
ITEM_MAX_DEMAND = "Maximum demand"
ITEM_METER_EXP  = "Meter data export"
# Exact text from Analysis dropdown — check both possible names
ITEM_TARGET_VS_OPTIONS = ["Target vs actual energy", "Target Vs Actual Energy",
                          "Target vs Actual Energy", "Target Vs actual energy"]

ocr = ddddocr.DdddOcr(beta=True, show_ad=False)

# ─────────────────────────────────────────
# DATE HELPERS
# ─────────────────────────────────────────
def fmt_date(dt) -> str:
    return f"{dt.month}/{dt.day}/{dt.year}"

def yesterday_str() -> str:
    return fmt_date(datetime.now() - timedelta(days=1))

def today_str() -> str:
    return fmt_date(datetime.now())

def first_of_month_str() -> str:
    return fmt_date(datetime.now().replace(day=1))

def prev_two_months():
    now = datetime.now()
    m, y = now.month, now.year
    if m == 1:
        to_m, to_y = 12, y - 1
        from_m, from_y = 11, y - 1
    elif m == 2:
        to_m, to_y = 1, y
        from_m, from_y = 12, y - 1
    else:
        to_m, to_y = m - 1, y
        from_m, from_y = m - 2, y
    return from_m, from_y, to_m, to_y

# ─────────────────────────────────────────
# CAPTCHA
# ─────────────────────────────────────────
def _preprocess(image_bytes: bytes, contrast: float = 2.0, sharpen: bool = False) -> bytes:
    from PIL import ImageEnhance, ImageFilter
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    img = ImageEnhance.Contrast(img).enhance(contrast)
    if sharpen:
        img = img.filter(ImageFilter.SHARPEN)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def _most_confident(candidates: list) -> str:
    from collections import Counter
    counts = Counter(candidates)
    top, freq = counts.most_common(1)[0]
    if freq > 1:
        return top
    for c in candidates:
        if not c.isdigit():
            return c
    return candidates[0]

CAPTCHA_CHAR_FIXES = {
    "A": "a", "z": "1", "Z": "1", "G": "6", "g": "6",
}

def _fix_chars(text: str) -> str:
    return "".join(CAPTCHA_CHAR_FIXES.get(ch, ch) for ch in text)

def solve_captcha(image_bytes: bytes) -> str:
    variants = [
        image_bytes,
        _preprocess(image_bytes, contrast=1.5),
        _preprocess(image_bytes, contrast=2.5),
        _preprocess(image_bytes, contrast=2.0, sharpen=True),
    ]
    reads = []
    for i, v in enumerate(variants):
        try:
            r = ocr.classification(v).strip().replace(" ", "")
            r = re.sub(r"[^A-Za-z0-9]", "", r)
            reads.append(r)
            print(f"  🔬 Variant {i+1}: '{r}'")
        except Exception as e:
            print(f"  🔬 Variant {i+1} failed: {e}")
    if not reads:
        print("  ⚠️  All OCR variants failed")
        return ""
    best = _fix_chars(_most_confident(reads))
    print(f"🤖 Final captcha: '{best}'")
    return best

# ─────────────────────────────────────────
# CLEANUP
# ─────────────────────────────────────────
def cleanup_debug_images():
    for fname in os.listdir(BASE_DIR):
        if fname.startswith(("captcha_", "screen_", "_captcha_")):
            try: os.remove(os.path.join(BASE_DIR, fname))
            except: pass
    print("🧹 Debug images cleaned up")

def delete_old_files(prefix: str):
    """Delete any existing files matching prefix_*.xls/xlsx in SAVE_DIR"""
    for fname in os.listdir(SAVE_DIR):
        if fname.startswith(prefix) and fname.endswith((".xls", ".xlsx")):
            try:
                os.remove(os.path.join(SAVE_DIR, fname))
                print(f"  🗑️  Deleted old: {fname}")
            except: pass    

# ─────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────
def login(page) -> bool:
    page.goto(LOGIN_URL, timeout=60000)
    page.wait_for_timeout(3000)

    attempt = 0
    while True:
        attempt += 1
        print(f"\n🔐 Attempt {attempt}...")

        filled_user = False
        try:
            f = page.get_by_label("Login ID")
            if f.is_visible():
                f.click(click_count=3); f.fill(USERNAME)
                filled_user = True
        except: pass
        if not filled_user:
            for inp in page.locator("input[type='text'], input:not([type])").all():
                try:
                    placeholder = inp.get_attribute("placeholder") or ""
                    name = inp.get_attribute("name") or ""
                    if inp.is_visible() and ("login" in placeholder.lower() or "login" in name.lower() or "user" in name.lower()):
                        inp.click(click_count=3)
                        inp.fill(USERNAME)
                        break
                except: pass

        filled_pass = False
        try:
            f = page.get_by_label("Password")
            if f.is_visible():
                f.click(click_count=3); f.fill(PASSWORD)
                filled_pass = True
        except: pass
        if not filled_pass:
            for inp in page.locator("input[type='password']").all():
                try:
                    if inp.is_visible():
                        inp.click(click_count=3); inp.fill(PASSWORD)
                        break
                except: pass

        captcha_input_el = None
        try:
            f = page.get_by_label("Captcha")
            if f.is_visible():
                captcha_input_el = f
        except: pass
        if not captcha_input_el:
            text_inputs = [
                inp for inp in page.locator(
                    "input[type='text'], input:not([type='password']):not([type='submit'])"
                    ":not([type='button']):not([type='hidden'])"
                ).all()
                if inp.is_visible()
            ]
            if text_inputs:
                captcha_input_el = text_inputs[-1]

        if captcha_input_el:
            captcha_input_el.click()
            page.keyboard.press("ControlOrMeta+A")
            page.keyboard.press("Backspace")
            print("  👆 Cleared captcha field. Waiting 2.5s...")
            page.wait_for_timeout(2500)

        captcha_text = ""
        for sel in [
            "img[id*='captcha' i]", "img[src*='captcha' i]",
            "img[src*='Captcha']", "img[src*='ValidateImage' i]",
            "img[src*='verify' i]", "img[alt*='captcha' i]",
        ]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1500):
                    captcha_text = solve_captcha(el.screenshot())
                    break
            except: pass

        if captcha_text and captcha_input_el:
            try:
                captcha_input_el.focus()
                page.keyboard.type(captcha_text, delay=150)
            except: pass

        login_clicked = False
        try:
            btn = page.get_by_role("button", name="Login")
            if btn.is_visible(timeout=2000):
                btn.click()
                login_clicked = True
        except: pass
        if not login_clicked:
            for sel in ["input[type='submit']", "button[type='submit']",
                        "button:has-text('Login')", "input[value='Login']"]:
                try:
                    b = page.locator(sel).first
                    if b.is_visible(timeout=1000):
                        b.click(); login_clicked = True; break
                except: pass

        page.wait_for_timeout(4000)

        try:
            for btn_text in ["Continue", "continue", "OK", "Ok", "Yes", "yes"]:
                el = page.locator(f"text='{btn_text}'").first
                if el.is_visible(timeout=2000):
                    print(f"  ⚠️ Session popup: clicking '{btn_text}'...")
                    el.click()
                    page.wait_for_timeout(4000)
                    break
        except: pass

        url        = page.url.lower()
        body_lower = page.inner_text("body").lower()

        if "login=1" not in url or "dashboard" in url or "home" in url:
            print("✅ Login successful!")
            cleanup_debug_images()
            return True
        if not any(k in body_lower for k in ["invalid","incorrect","wrong","error","failed"]):
            print("✅ No error — assuming logged in!")
            cleanup_debug_images()
            return True

        print("  ❌ Login failed. Refreshing...")
        refreshed = False
        for sel in ["img[src*='refresh' i]","img[onclick*='captcha' i]",
                    "span[onclick*='captcha' i]",".refresh","a[onclick*='captcha' i]"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1000):
                    el.click(); page.wait_for_timeout(2000)
                    refreshed = True; break
            except: pass
        if not refreshed:
            page.reload()
            page.wait_for_timeout(2000)

# ─────────────────────────────────────────
# WAIT HELPER
# ─────────────────────────────────────────
def w(page):
    page.wait_for_timeout(5000)

# ─────────────────────────────────────────
# NAVIGATE via top navbar + dropdown
# ─────────────────────────────────────────
def _find_nav_top(page, label: str):
    selectors = [
        f"nav a:has-text('{label}')",
        f".navbar a:has-text('{label}')",
        f".nav-item a:has-text('{label}')",
        f"#navbarNav a:has-text('{label}')",
        f"ul.navbar-nav a:has-text('{label}')",
        f"ul.nav a:has-text('{label}')",
    ]
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1500):
                return el
        except: pass
    try:
        for a in page.locator("a").all():
            try:
                if a.is_visible(timeout=300) and a.inner_text().strip() == label:
                    return a
            except: pass
    except: pass
    return None

def recover_session(page):
    """Try to recover by going back to homepage and re-navigating"""
    print("  🔄 Recovering session...")
    try:
        page.goto(BASE_URL, timeout=30000)
        page.wait_for_timeout(3000)
        # Check if we got logged out
        url = page.url.lower()
        body = page.inner_text("body").lower()
        if "login=1" in url or any(k in body for k in ["login id", "captcha", "password"]):
            print("  🔐 Session expired — re-logging in...")
            login(page)
        else:
            print("  ✅ Session recovered")
        return True
    except Exception as e:
        print(f"  ⚠️  Recovery failed: {e}")
        return False

def nav_to_report(page, top_menu: str, sub_item: str):
    """Navigate top_menu → sub_item. sub_item can be a str or list of candidate strings."""
    candidates = sub_item if isinstance(sub_item, list) else [sub_item]

    for attempt in range(1, 4):
        try:
            print(f"  🌐 Nav: {top_menu} → {candidates[0]} (attempt {attempt})")
            top = _find_nav_top(page, top_menu)
            if top is None:
                print(f"  ⚠️  Top nav '{top_menu}' not found")
                recover_session(page)
                page.wait_for_timeout(2000)
                continue
            top.hover()
            page.wait_for_timeout(1500)

            sub = None
            for name in candidates:
                for sel in [
                    f"a:has-text('{name}')",
                    f"li a:has-text('{name}')",
                    f".dropdown-menu a:has-text('{name}')",
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.is_visible(timeout=1500):
                            sub = el
                            print(f"  ✅ Found sub-item: '{name}'")
                            break
                    except: pass
                if sub:
                    break

            if sub is None:
                for name in candidates:
                    try:
                        for a in page.locator("a").all():
                            try:
                                txt = a.inner_text().strip()
                                if a.is_visible(timeout=200) and txt.lower() == name.lower():
                                    sub = a
                                    print(f"  ✅ Found sub-item (scan): '{txt}'")
                                    break
                            except: pass
                        if sub:
                            break
                    except: pass

            if sub is None:
                print(f"  ⚠️  Sub-item not visible after hover (attempt {attempt})")
                page.keyboard.press("Escape")
                page.wait_for_timeout(1500)
                if attempt == 2:
                    recover_session(page)
                continue

            sub.click()
            w(page)
            return True

        except Exception as e:
            print(f"  ⚠️  Nav attempt {attempt} error: {e}")
            page.keyboard.press("Escape")
            recover_session(page)
            page.wait_for_timeout(2000)

    print(f"  ❌ Failed to navigate: {top_menu} → {candidates[0]}")
    return False

# ─────────────────────────────────────────
# CLICK A TAB
# ─────────────────────────────────────────
def click_tab(page, label: str):
    # Exact text match on any visible <a>
    try:
        for a in page.locator("a").all():
            try:
                if a.is_visible(timeout=300) and a.inner_text().strip() == label:
                    a.click()
                    w(page)
                    print(f"  📑 Tab: '{label}'")
                    return True
            except: pass
    except: pass
    for sel in [
        f"a:has-text('{label}')",
        f"li:has-text('{label}') a",
        f"li:has-text('{label}')",
        f"span:has-text('{label}')",
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click()
                w(page)
                print(f"  📑 Tab (has-text): '{label}'")
                return True
        except: pass
    print(f"  ⚠️  Tab not found: '{label}'")
    return False

# ─────────────────────────────────────────
# DATE FIELDS — standard From/To date text inputs
# ─────────────────────────────────────────
def set_from_to(page, from_str: str, to_str: str):
    def fill_input(inp_el, value):
        try:
            inp_el.evaluate(f"""el => {{
                var nv = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value');
                nv.set.call(el, '{value}');
                el.dispatchEvent(new Event('input',  {{bubbles:true}}));
                el.dispatchEvent(new Event('change', {{bubbles:true}}));
                el.dispatchEvent(new Event('blur',   {{bubbles:true}}));
            }}""")
            page.wait_for_timeout(400)
        except: pass
        try:
            inp_el.click(click_count=3)
            inp_el.fill(value)
            inp_el.press("Tab")
            page.wait_for_timeout(400)
        except: pass

    from_inp = to_inp = None
    for lbl in page.locator("label, td, span, div").all():
        try:
            txt = lbl.inner_text().strip().lower()
            if txt in ("from date", "from date*", "from", "from date :"):
                inp = lbl.locator("xpath=following::input[@type='text'][1]").first
                if inp.is_visible(timeout=1000):
                    from_inp = inp
            elif txt in ("to date", "to date*", "to", "to date :"):
                inp = lbl.locator("xpath=following::input[@type='text'][1]").first
                if inp.is_visible(timeout=1000):
                    to_inp = inp
        except: pass
        if from_inp and to_inp:
            break

    if not from_inp or not to_inp:
        date_inputs = []
        for inp in page.locator("input[type='text']").all():
            try:
                val = inp.input_value()
                if inp.is_visible() and ("/" in val or val == ""):
                    date_inputs.append(inp)
            except: pass
        if len(date_inputs) >= 2:
            from_inp = date_inputs[0]
            to_inp   = date_inputs[1]
        elif len(date_inputs) == 1:
            from_inp = date_inputs[0]

    if from_inp:
        fill_input(from_inp, from_str)
        print(f"  📅 From date: {from_str}")
    else:
        print(f"  ⚠️  From date input not found")

    if to_inp:
        fill_input(to_inp, to_str)
        print(f"  📅 To date: {to_str}")
    else:
        print(f"  ⚠️  To date input not found")

    w(page)

# ─────────────────────────────────────────
# MONTH/YEAR SELECTS
# Used by: Cons/Gen Monthly, Shiftwise Monthly, Target vs Actual Monthly
# ─────────────────────────────────────────
def set_from_to_month_year(page, from_m: int, from_y: int, to_m: int, to_y: int):
    month_names = ["", "January","February","March","April","May","June",
                   "July","August","September","October","November","December"]

    all_selects = []
    for s in page.locator("select").all():
        try:
            if s.is_visible(timeout=500):
                all_selects.append(s)
        except: pass

    print(f"  📋 Found {len(all_selects)} visible selects for month/year")

    month_selects = []
    year_selects  = []
    for s in all_selects:
        try:
            opts = [o.inner_text().strip() for o in s.locator("option").all()]
            opts_lower = [o.lower() for o in opts]
            # Check if it's a month select
            if any(m.lower() in opts_lower for m in month_names[1:]):
                month_selects.append((s, opts))
            # Check if it's a year select
            elif any(str(y) in opts for y in range(2020, 2030)):
                year_selects.append((s, opts))
        except: pass

    print(f"  📋 Month selects: {len(month_selects)}, Year selects: {len(year_selects)}")

    if len(month_selects) >= 2:
        try:
            month_selects[0][0].select_option(label=month_names[from_m])
            page.wait_for_timeout(500)
            print(f"  📅 From month: {month_names[from_m]}")
        except Exception as e:
            print(f"  ⚠️  From month: {e}")
        try:
            month_selects[1][0].select_option(label=month_names[to_m])
            page.wait_for_timeout(500)
            print(f"  📅 To month: {month_names[to_m]}")
        except Exception as e:
            print(f"  ⚠️  To month: {e}")
    elif len(month_selects) == 1:
        try:
            month_selects[0][0].select_option(label=month_names[from_m])
            page.wait_for_timeout(500)
        except: pass

    if len(year_selects) >= 2:
        try:
            year_selects[0][0].select_option(label=str(from_y))
            page.wait_for_timeout(500)
            print(f"  📅 From year: {from_y}")
        except Exception as e:
            print(f"  ⚠️  From year: {e}")
        try:
            year_selects[1][0].select_option(label=str(to_y))
            page.wait_for_timeout(500)
            print(f"  📅 To year: {to_y}")
        except Exception as e:
            print(f"  ⚠️  To year: {e}")

    w(page)

# ─────────────────────────────────────────
# RADIO — select Actual
# ─────────────────────────────────────────
def select_actual_radio(page):
    for r in page.locator("input[type='radio']").all():
        try:
            lbl = r.evaluate(
                "el => el.nextElementSibling?.textContent"
                "   || el.labels?.[0]?.textContent"
                "   || el.value || ''"
            )
            if "actual" in str(lbl).lower():
                r.check()
                page.wait_for_timeout(1000)
                print("  🔘 Actual radio selected")
                return True
        except: pass
    return False

# ─────────────────────────────────────────
# PARAMETER DROPDOWN
# Matches 'Abs Active' against 'Abs Active Energy' on site
# ─────────────────────────────────────────
def select_parameter(page, option_text: str):
    param_kw = ["active", "energy", "demand", "power", "reactive", "apparent", "total"]
    for dd in page.locator("select").all():
        try:
            if not dd.is_visible(timeout=500):
                continue
            opts = [o.inner_text().strip() for o in dd.locator("option").all()]
            if not any(any(kw in o.lower() for kw in param_kw) for o in opts):
                continue
            match = next((o for o in opts if option_text.lower() in o.lower()), None)
            if match:
                dd.select_option(label=match)
                w(page)
                print(f"  ⚙️  Parameter: '{match}'")
                return True
        except: pass
    print(f"  ⚠️  Parameter '{option_text}' not found")
    return False

# ─────────────────────────────────────────
# DATA TYPE DROPDOWN
# ─────────────────────────────────────────
def select_data_type(page, option_text: str):
    dtype_kw = ["consumption", "generation", "reading", "load", "duration"]
    for dd in page.locator("select").all():
        try:
            if not dd.is_visible(timeout=500):
                continue
            opts = [o.inner_text().strip() for o in dd.locator("option").all()]
            if not any(any(kw in o.lower() for kw in dtype_kw) for o in opts):
                continue
            match = next((o for o in opts if option_text.lower() in o.lower()), None)
            if match:
                dd.select_option(label=match)
                w(page)
                print(f"  🗂️  Data type: '{match}'")
                return True
        except: pass
    print(f"  ⚠️  Data type '{option_text}' not found")
    return False

# ─────────────────────────────────────────
# SINGLE-SELECT LOCATION DROPDOWN (Saving interval wise)
# ─────────────────────────────────────────
def select_location_dropdown(page, location_text: str):
    key = location_text.strip().upper()[:6]
    skip_kw = ["active","energy","demand","power","reading","load","duration",
               "generation","consumption","reactive","apparent","total"]
    for dd in page.locator("select").all():
        try:
            if not dd.is_visible(timeout=500):
                continue
            sz = int(dd.evaluate("el => el.size || 1"))
            if sz > 1:
                continue
            opts = [o.inner_text().strip() for o in dd.locator("option").all()]
            if not any(key in o.upper() for o in opts):
                continue
            if any(any(kw in o.lower() for kw in skip_kw) for o in opts):
                continue
            match = next((o for o in opts if key in o.upper()), None)
            if match:
                dd.select_option(label=match)
                w(page)
                print(f"  📍 Dropdown location: '{match}'")
                return True
        except: pass
    print(f"  ⚠️  Dropdown location '{location_text}' not found")
    return False

# ─────────────────────────────────────────
# DUAL LISTBOX — move one location to right
# ─────────────────────────────────────────
def move_to_right(page, location_text: str):
    key = location_text.strip().upper()
    selected = False
    try:
        listboxes = []
        for s in page.locator("select").all():
            try:
                if not s.is_visible(timeout=500):
                    continue
                sz = int(s.evaluate("el => el.size || 1"))
                if sz > 1:
                    listboxes.append(s)
            except: pass

        if listboxes:
            left = listboxes[0]
            opts = [o.inner_text().strip() for o in left.locator("option").all()]
            print(f"  📋 Left listbox: {opts}")
            match = next((o for o in opts if o.strip().upper() == key), None)
            if not match:
                match = next((o for o in opts if key[:6] in o.upper()), None)
            if match:
                left.select_option(label=match)
                page.wait_for_timeout(800)
                selected = True
                print(f"  👈 Selected: '{match}'")
            else:
                print(f"  ⚠️  '{location_text}' not in left list: {opts}")
    except Exception as e:
        print(f"  ⚠️  Left-list error: {e}")

    if not selected:
        return False

    for btn_sel in [
        "input[type='button'][value='>']",
        "input[value='>']",
        "button:has-text('>')",
    ]:
        try:
            btn = page.locator(btn_sel).first
            if btn.is_visible(timeout=3000):
                btn.click()
                page.wait_for_timeout(2000)
                print(f"  ➡️  Moved '{location_text}' to right")
                return True
        except: pass

    print(f"  ⚠️  > button not found")
    return False

def move_both_to_right(page):
    move_to_right(page, "INSTITUTIONAL Area")
    move_to_right(page, "RESIDENTIAL AREA")

def clear_right_list(page):
    try:
        listboxes = []
        for s in page.locator("select").all():
            try:
                if not s.is_visible(timeout=500):
                    continue
                sz = int(s.evaluate("el => el.size || 1"))
                if sz > 1:
                    listboxes.append(s)
            except: pass

        if len(listboxes) >= 2:
            right = listboxes[1]
            opts  = right.locator("option").all()
            count = len(opts)
            if count > 0:
                right.select_option(index=list(range(count)))
                page.wait_for_timeout(500)
                for btn_sel in [
                    "input[type='button'][value='<']",
                    "input[value='<']",
                    "button:has-text('<')",
                ]:
                    try:
                        btn = page.locator(btn_sel).first
                        if btn.is_visible(timeout=2000):
                            btn.click()
                            page.wait_for_timeout(1500)
                            print("  ⬅️  Right list cleared")
                            return True
                    except: pass
            else:
                print("  ✓ Right list already empty")
                return True
    except Exception as e:
        print(f"  ⚠️  clear_right_list: {e}")
    return False

# ─────────────────────────────────────────
# FIND AND CLICK DOWNLOAD/EXPORT BUTTON
# Handles both "Generate Report" (Reports pages) and
# "Export" top-right link (Analysis pages)
# ─────────────────────────────────────────
def _find_action_button(page):
    """
    Returns the element to click for downloading.
    Tries Generate Report first, then Export (top-right).
    The Export link on Analysis pages is a plain <a> with text 'Export'
    positioned at top-right — matched by text content.
    """
    # Generate Report button (Reports pages)
    for sel in [
        "a:has-text('Generate Report')",
        "input[value='Generate Report']",
        "button:has-text('Generate Report')",
    ]:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=2000):
                print(f"  🖱️  Found: {sel}")
                return btn
        except: pass

    # Export link — Analysis pages (top-right corner plain <a> tag)
    # From screenshot: it's just <a class="...">Export</a> top-right
    for sel in [
        "a:has-text('Export')",
        "button:has-text('Export')",
        "input[value='Export']",
        "a[id*='Export' i]",
        "input[id*='Export' i]",
        "button[id*='Export' i]",
    ]:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=2000):
                print(f"  🖱️  Found: {sel}")
                return btn
        except: pass

    # Last resort: scan ALL visible <a> tags for exact text 'Export'
    try:
        for a in page.locator("a").all():
            try:
                if a.is_visible(timeout=200) and a.inner_text().strip() == "Export":
                    print(f"  🖱️  Found Export via scan")
                    return a
            except: pass
    except: pass

    print(f"  ⚠️  No download/export button found")
    return None

# ─────────────────────────────────────────
# DOWNLOAD — 20 second timeout then proceed
# ─────────────────────────────────────────
def wait_and_save_download(page, prefix: str, timeout: int = 20000, date_tag: str = ""):
    """
    date_tag controls the filename:
      ""         → no date → always overwrites same file (saving interval wise)
      "20250603" → overwrites when the date changes (daily/monthly)
    """
    suffix = f"_{date_tag}" if date_tag else ""
    filename_base = f"{prefix}{suffix}"
    print(f"  ⬇️  Waiting for download: '{filename_base}'...")
    try:
        with page.expect_download(timeout=timeout) as dl_info:
            btn = _find_action_button(page)
            if btn:
                btn.click()
            else:
                print(f"  ⚠️  Skipping click — button not found")

        dl   = dl_info.value
        ext  = os.path.splitext(dl.suggested_filename)[1] or ".xls"
        delete_old_files(prefix)
        path = os.path.join(SAVE_DIR, f"{filename_base}{ext}")
        dl.save_as(path)
        print(f"  ✅ Saved: {path}")
        return path
    except Exception as e:
        print(f"  ⚠️  Download timed out / failed for '{filename_base}' (20s): {e}")
        print(f"  ⏭️  Proceeding to next step...")
        return None

# ═══════════════════════════════════════════════════════════
# STEP 1 — REPORTS → CONSUMPTION / GENERATION
#
# Saving interval wise: single-select dropdown, one download per area
# Daily: both areas in right box → one download (yesterday)
# Monthly: month+year dropdowns, both areas → one download
# ═══════════════════════════════════════════════════════════
def do_consumption_generation(page):
    print("\n" + "="*60)
    print("📥 STEP 1/5 — Reports → Consumption / Generation")
    print("="*60)

    today = today_str()
    yest  = yesterday_str()
    from_m, from_y, to_m, to_y = prev_two_months()

    yest_tag  = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    month_tag = f"{from_y}{from_m:02d}_{to_y}{to_m:02d}"

    # Saving interval wise — no date tag → always overwrites same file
    for area, area_key in [("INSTITUTIONAL Area", "institutional"), ("RESIDENTIAL AREA", "residential")]:
        print(f"\n  ▶ Saving interval wise | {area} | {today}")
        nav_to_report(page, MENU_REPORTS, ITEM_CONS_GEN)
        click_tab(page, "Saving interval wise")
        set_from_to(page, today, today)
        select_actual_radio(page)
        select_parameter(page, "Abs Active")
        select_location_dropdown(page, area)
        wait_and_save_download(page, f"cons_gen_saving_interval_{area_key}")  # no date_tag

    # Daily — overwrites when yesterday's date changes
    print(f"\n  ▶ Daily | BOTH areas | {yest}")
    nav_to_report(page, MENU_REPORTS, ITEM_CONS_GEN)
    click_tab(page, "Daily")
    set_from_to(page, yest, yest)
    select_actual_radio(page)
    select_parameter(page, "Abs Active")
    clear_right_list(page)
    move_both_to_right(page)
    wait_and_save_download(page, "cons_gen_daily", date_tag=yest_tag)  # e.g. cons_gen_daily_20250603

    # Monthly — overwrites when month changes
    print(f"\n  ▶ Monthly | BOTH areas | {from_m}/{from_y} → {to_m}/{to_y}")
    nav_to_report(page, MENU_REPORTS, ITEM_CONS_GEN)
    click_tab(page, "Monthly")
    set_from_to_month_year(page, from_m, from_y, to_m, to_y)
    select_actual_radio(page)
    select_parameter(page, "Abs Active")
    clear_right_list(page)
    move_both_to_right(page)
    wait_and_save_download(page, "cons_gen_monthly", date_tag=month_tag)  # e.g. cons_gen_monthly_202504_202505

# ═══════════════════════════════════════════════════════════
# STEP 2 — REPORTS → MAXIMUM DEMAND
#
# Saving interval wise: single-select dropdown, one download per area
# Daily: both areas together (yesterday)
# ═══════════════════════════════════════════════════════════
def do_maximum_demand(page):
    print("\n" + "="*60)
    print("📥 STEP 2/5 — Reports → Maximum Demand")
    print("="*60)

    today = today_str()
    yest  = yesterday_str()

    # Saving interval wise — separate per area
    for area, area_key in [("INSTITUTIONAL Area", "institutional"), ("RESIDENTIAL AREA", "residential")]:
        print(f"\n  ▶ Saving interval wise | {area} | {today}")
        nav_to_report(page, MENU_REPORTS, ITEM_MAX_DEMAND)
        click_tab(page, "Saving interval wise")
        set_from_to(page, today, today)
        select_actual_radio(page)
        if not select_parameter(page, "Demand - Abs Active"):
            select_parameter(page, "Abs Active")
        select_location_dropdown(page, area)
        wait_and_save_download(page, f"max_demand_saving_interval_{area_key}")
        w(page)

    # Daily — both areas together
    print(f"\n  ▶ Daily | BOTH areas | {yest}")
    nav_to_report(page, MENU_REPORTS, ITEM_MAX_DEMAND)
    click_tab(page, "Daily")
    set_from_to(page, yest, yest)
    select_actual_radio(page)
    if not select_parameter(page, "Demand - Abs Active"):
        select_parameter(page, "Abs Active")
    clear_right_list(page)
    move_both_to_right(page)
    wait_and_save_download(page, "max_demand_daily")
    w(page)

# ═══════════════════════════════════════════════════════════
# STEP 3 — REPORTS → SHIFTWISE CONSUMPTION / GENERATION
#
# Daily shiftwise: yesterday, both areas together
# Monthly: month+year dropdowns (NOT date textboxes), both areas
# ═══════════════════════════════════════════════════════════
def do_shiftwise(page):
    print("\n" + "="*60)
    print("📥 STEP 3/5 — Reports → Shiftwise Consumption / Generation")
    print("="*60)

    yest = yesterday_str()
    from_m, from_y, to_m, to_y = prev_two_months()

    # Daily shiftwise — yesterday, both areas
    print(f"\n  ▶ Daily shiftwise | BOTH areas | {yest}")
    nav_to_report(page, MENU_REPORTS, ITEM_SHIFTWISE)
    click_tab(page, "Daily shiftwise")
    set_from_to(page, yest, yest)
    select_actual_radio(page)
    select_parameter(page, "Abs Active")
    clear_right_list(page)
    move_both_to_right(page)
    wait_and_save_download(page, "shiftwise_daily")
    w(page)

    # Monthly — month+year dropdowns, both areas
    print(f"\n  ▶ Monthly | BOTH areas | {from_m}/{from_y} → {to_m}/{to_y}")
    nav_to_report(page, MENU_REPORTS, ITEM_SHIFTWISE)
    click_tab(page, "Monthly")
    set_from_to_month_year(page, from_m, from_y, to_m, to_y)
    select_actual_radio(page)
    select_parameter(page, "Abs Active")
    clear_right_list(page)
    move_both_to_right(page)
    wait_and_save_download(page, "shiftwise_monthly")
    w(page)

# ═══════════════════════════════════════════════════════════
# STEP 4 — ANALYSIS → METER DATA EXPORT
#
# Export button = top-right <a>Export</a> link (NOT Generate Report)
# Both areas together, all 3 data types
# ═══════════════════════════════════════════════════════════
def do_meter_data_export(page):
    print("\n" + "="*60)
    print("📥 STEP 4/5 — Analysis → Meter Data Export")
    print("="*60)

    yest = yesterday_str()

    data_types = [
        ("Consumption/Generation", "cons_gen"),
        ("Reading",                "reading"),
        ("Load off duration",      "load_off"),
    ]

    for dtype_label, dtype_key in data_types:
        print(f"\n  ▶ Data type: {dtype_label} | BOTH areas | {yest}")
        nav_to_report(page, MENU_ANALYSIS, ITEM_METER_EXP)
        set_from_to(page, yest, yest)
        select_actual_radio(page)
        select_parameter(page, "Abs Active")
        select_data_type(page, dtype_label)
        clear_right_list(page)
        move_both_to_right(page)
        wait_and_save_download(page, f"meter_export_{dtype_key}")
        w(page)

# ═══════════════════════════════════════════════════════════
# STEP 5 — ANALYSIS → TARGET VS ACTUAL ENERGY
#
# Export button = top-right <a>Export</a> link
# Tries multiple possible menu item name variants
# Hourly: today | Daily: first of month → today | Monthly: month+year dropdowns
# Both areas together for all tabs
# ═══════════════════════════════════════════════════════════
def do_target_vs_actual(page):
    print("\n" + "="*60)
    print("📥 STEP 5/5 — Analysis → Target vs Actual Energy")
    print("="*60)

    today = today_str()
    fom   = first_of_month_str()
    from_m, from_y, to_m, to_y = prev_two_months()

    # First — navigate once to discover the exact menu text
    print("  🔍 Discovering Target vs Actual menu item name...")
    target_nav_name = None
    top = _find_nav_top(page, MENU_ANALYSIS)
    if top:
        top.hover()
        page.wait_for_timeout(1500)
        try:
            for a in page.locator("a").all():
                try:
                    txt = a.inner_text().strip()
                    if a.is_visible(timeout=200) and "target" in txt.lower() and "actual" in txt.lower():
                        target_nav_name = txt
                        print(f"  ✅ Found menu item: '{txt}'")
                        break
                except: pass
        except: pass
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    if not target_nav_name:
        target_nav_name = ITEM_TARGET_VS_OPTIONS  # fallback to list
        print(f"  ⚠️  Could not auto-detect, will try all variants")

    configs = [
        ("Hourly",  "hourly",  False, today, today),
        ("Daily",   "daily",   False, today, today),
        ("Monthly", "monthly", True,  None,  None),
    ]

    for tab_label, tab_key, use_my, from_d, to_d in configs:
        print(f"\n  ▶ {tab_label} | BOTH areas")
        nav_to_report(page, MENU_ANALYSIS, target_nav_name)
        click_tab(page, tab_label)
        if use_my:
            set_from_to_month_year(page, from_m, from_y, to_m, to_y)
        else:
            set_from_to(page, from_d, to_d)
        select_actual_radio(page)
        select_parameter(page, "Abs Active")
        clear_right_list(page)
        move_both_to_right(page)
        wait_and_save_download(page, f"target_vs_actual_{tab_key}")
        w(page)

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=300)
        ctx = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080}
        )
        page = ctx.new_page()

        login(page)
        page.wait_for_timeout(5000)

        do_consumption_generation(page)
        do_maximum_demand(page)
        do_shiftwise(page)
        do_meter_data_export(page)
        do_target_vs_actual(page)

        print(f"\n✅ All downloads complete. Files in: {SAVE_DIR}")
        browser.close()

# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    once_mode = "--once" in sys.argv

    if once_mode:
        print("🚀 eWatch — single cycle.\n")
        try:
            scrape()
        except Exception as e:
            print(f"🚨 Crashed: {e}")
        sys.exit(0)
    else:
        print(f"🚀 eWatch — 30-min loop.\n📁 Output: {SAVE_DIR}\n")
        while True:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'='*60}\n🔄 Cycle at: {ts}\n{'='*60}")
            try:
                scrape()
            except Exception as e:
                print(f"🚨 Cycle crashed: {e}. Retrying next cycle.")
            print("\n⏳ Waiting 30 minutes...")
            time.sleep(30 * 60)