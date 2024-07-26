import threading
import subprocess
import sys
import time
from armchecker import ArmChecker
from downloadlogs import DownloadLogs

def run_upload_logs():
    while True:
        subprocess.run([sys.executable, "upload_logs.py"])

class Executor:
    def __init__(self, connection_string):
        self.arm_checker = ArmChecker(connection_string)
        self.download_logs = DownloadLogs(connection_string)
        self.location_process = None
        self.str_rec_process = None

    def run(self):
        # Start the upload_logs.py script in a separate thread
        upload_thread = threading.Thread(target=run_upload_logs, daemon=True)
        upload_thread.start()

        while True:
            arm_status, status_changed = self.arm_checker.get_arm_status()
            
            if status_changed:
                if arm_status:
                    print("\n*** ARM CONDITION TRIGGERED ***")
                    print("Drone has been armed!")
                    self.download_logs.stop()
                    print("Stopped log download.")
                    if self.location_process is None or self.location_process.poll() is not None:
                        print("Starting location.py...")
                        self.location_process = subprocess.Popen([sys.executable, "location.py"])
                    if self.str_rec_process is None or self.str_rec_process.poll() is not None:
                        print("Starting str+rec_new.py...")
                        self.str_rec_process = subprocess.Popen([sys.executable, "str+rec_new.py"])
                else:
                    print("\n*** DISARM CONDITION TRIGGERED ***")
                    print("Drone has been disarmed!")
                    if self.location_process:
                        print("Stopping location.py...")
                        self.location_process.terminate()
                        self.location_process = None
                    if self.str_rec_process:
                        print("Stopping str+rec_new.py...")
                        self.str_rec_process.terminate()
                        self.str_rec_process = None
                    print("Starting log download...")
                    self.download_logs.start()
            
            time.sleep(5)

def main():
    executor = Executor('/dev/ttyACM0')
    executor.run()

if __name__ == "__main__":
    print(sys.version)  # Print Python version for debugging
    main()