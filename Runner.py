import time
import subprocess
import datetime
import sys

PYTHON_EXE = sys.executable 
SCRIPT_NAME = "5feb_auto.py" 
INTERVAL_SECONDS = 15 * 60 

print("==========================================")
print(" iSolarCloud Auto Downloader Started ")
print("==========================================")

while True:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{now}] Attempting download...")

    try:
        # check=True will raise a CalledProcessError if the script fails
        subprocess.run([PYTHON_EXE, SCRIPT_NAME], check=True)
        print(f"✔ [{now}] Download completed successfully")
    except subprocess.CalledProcessError as e:
        # This catches the ERR_NAME_NOT_RESOLVED or any other script crash
        print(f"❌ [{now}] Script failed (likely Network/DNS issue).")
        print(f"   Error details: {e}")
    except Exception as e:
        print(f"⚠️ An unexpected error occurred: {e}")

    print(f"⏳ Waiting 15 minutes until next run...")
    try:
        time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopping the runner. Goodbye!")
        break