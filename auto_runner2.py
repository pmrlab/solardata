import time
import subprocess
import datetime
import sys

PYTHON_EXE = sys.executable       # uses current python automatically

SCRIPTS = [
    "5feb_auto.py",                # iSolarCloud downloader
    "havells_crawling.py",         # Havells downloader
]

INTERVAL_SECONDS = 15 * 60        # 15 minutes between successful runs

MAX_RETRIES = 5                    # max retries per cycle on failure
RETRY_WAIT_SECONDS = 10           # wait 10s between retries

print("==========================================")
print(" Solar Auto Downloader Started ")
print(" Scripts: iSolarCloud + Havells ")
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
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                subprocess.run([PYTHON_EXE, script], check=True)
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

    print(f"\n✅ Cycle complete. Waiting {INTERVAL_SECONDS // 60} minutes for next cycle...\n")
    time.sleep(INTERVAL_SECONDS)