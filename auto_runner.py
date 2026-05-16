import time
import subprocess
import datetime
import sys

PYTHON_EXE = sys.executable   # uses current python automatically
SCRIPT_NAME = "5feb_auto.py"  # your existing script
INTERVAL_SECONDS = 15 * 60    # 15 minutes


print("==========================================")
print(" iSolarCloud Auto Downloader Started ")
print(" Interval: 15 minutes")
print(" Press CTRL+C to stop")
print("==========================================")

while True:
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{start_time}] Running download script...")

    try:
        subprocess.run([PYTHON_EXE, SCRIPT_NAME], check=True)
        print("✔ Download completed successfully")
    except Exception as e:
        print("❌ Download failed:", e)

    print("⏳ Waiting 15 minutes...\n")
    time.sleep(INTERVAL_SECONDS)
