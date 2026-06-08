import time
import subprocess
import datetime
import sys

PYTHON_EXE = sys.executable       # uses current python automatically

SCRIPTS = [
    "5feb_auto.py",                # iSolarCloud downloader
    "havells_crawling.py",         # Havells downloader
    "ewatch_scraper.py",           # eWatch downloader — runs after Havells
]

INTERVAL_SECONDS   = 30 * 60      # 30 minutes between cycles
MAX_RETRIES        = 5            # max retries per script on failure
RETRY_WAIT_SECONDS = 10           # wait 10s between retries

print("==========================================")
print(" Solar Auto Downloader Started ")
print(" Scripts: iSolarCloud + Havells + eWatch ")
print(f" Interval: {INTERVAL_SECONDS // 60} minutes")
print(f" Retry on failure: up to {MAX_RETRIES}x (every {RETRY_WAIT_SECONDS}s)")
print(" Press CTRL+C to stop")
print("==========================================")

while True:
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{start_time}] Starting download cycle...")

    for script in SCRIPTS:
        print(f"\n── Running: {script} ──")
        success = False

        # ewatch_scraper.py has its own internal loop when run standalone.
        # Pass --once so it runs a single cycle and exits cleanly here.
        args = [PYTHON_EXE, script]
        if script == "ewatch_scraper.py":
            args.append("--once")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                subprocess.run(args, check=True)
                print(f"✔ {script} completed successfully")
                success = True
                break
            except Exception as e:
                print(f"❌ Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    print(f"⏳ Retrying in {RETRY_WAIT_SECONDS}s...")
                    time.sleep(RETRY_WAIT_SECONDS)
                else:
                    print(f"🚨 All retries exhausted for {script}. Moving on.")

    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n✅ Cycle complete at {end_time}.")
    print(f"⏳ Waiting {INTERVAL_SECONDS // 60} minutes for next cycle...\n")
    time.sleep(INTERVAL_SECONDS)