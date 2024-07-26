import os
import pickle
import time
from pymavlink import mavutil

LOG_DIR = "/media/koustav/Koustav/4G/5G/Logs/LOG_FILES"
TRACKING_FILE = os.path.join(LOG_DIR, "downloaded_logs.pkl")

def ensure_dir_exists(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except PermissionError:
            print(f"Error: No permission to create directory {directory}")
            return False
    if not os.access(directory, os.W_OK):
        print(f"Error: No write permission for directory {directory}")
        return False
    return True

class DownloadLogs:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.master = None
        self.is_running = False
        if not ensure_dir_exists(LOG_DIR):
            raise PermissionError(f"Cannot access or create directory: {LOG_DIR}")
        self.downloaded_logs = self.load_downloaded_logs()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.master = mavutil.mavlink_connection(self.connection_string, baud=9600)
            self.download_logs()

    def stop(self):
        self.is_running = False
        if self.master:
            self.master.close()
            self.master = None

    def load_downloaded_logs(self):
        if os.path.exists(TRACKING_FILE):
            try:
                with open(TRACKING_FILE, 'rb') as f:
                    return pickle.load(f)
            except IOError as e:
                print(f"Error reading tracking file {TRACKING_FILE}: {e}")
        return set()

    def save_downloaded_logs(self):
        try:
            with open(TRACKING_FILE, 'wb') as f:
                pickle.dump(self.downloaded_logs, f)
        except IOError as e:
            print(f"Error saving tracking file {TRACKING_FILE}: {e}")

    def download_log(self, log_id, log_size, retry=3):
        log_file_path = os.path.join(LOG_DIR, f"log_{log_id}.bin")
        
        self.master.mav.log_request_data_send(
            target_system=1,
            target_component=0,
            id=log_id,
            ofs=0,
            count=0xFFFFFFFF
        )

        start_time = time.time()
        bytes_downloaded = 0

        try:
            with open(log_file_path, 'wb') as f:
                while self.is_running:
                    try:
                        msg = self.master.recv_match(type='LOG_DATA', blocking=True, timeout=30)
                        if msg is None:
                            print(f"\nTimeout occurred while downloading log {log_id}. Retrying...")
                            return False
                        data = bytes(msg.data)
                        f.write(data)
                        bytes_downloaded += len(data)
                        elapsed_time = time.time() - start_time
                        download_speed = bytes_downloaded / elapsed_time if elapsed_time > 0 else 0
                        print(f"\rDownloading log {log_id}: {bytes_downloaded / 1024:.2f} KB of {log_size / 1024:.2f} KB "
                              f"({bytes_downloaded / log_size * 100:.2f}%) at {download_speed / 1024:.2f} KB/s", end='')

                        if msg.ofs + len(msg.data) >= log_size:
                            break

                    except Exception as e:
                        print(f"\nError occurred while downloading log {log_id}: {e}")
                        if retry > 0:
                            print(f"Retrying... {retry} attempts left")
                            return self.download_log(log_id, log_size, retry-1)
                        else:
                            print("Maximum retries reached, skipping this log.")
                            return False

        except IOError as e:
            print(f"Error opening or writing to file {log_file_path}: {e}")
            return False

        elapsed_time = time.time() - start_time
        print(f"\nDownload of log {log_id} completed in {elapsed_time:.2f} seconds.")

        if os.path.getsize(log_file_path) > 0:
            print(f"Log {log_id} downloaded correctly.")
            return True
        else:
            print(f"Log {log_id} is empty.")
            os.remove(log_file_path)
            if retry > 0:
                print(f"Retrying download for log {log_id}... {retry-1} attempts left")
                return self.download_log(log_id, log_size, retry-1)
            else:
                print("Maximum retries reached, skipping this log.")
                return False

    def download_logs(self):
        while self.is_running:
            self.master.mav.log_request_list_send(
                target_system=1,
                target_component=0,
                start=0,
                end=0xffff
            )

            log_entries = []
            while self.is_running:
                msg = self.master.recv_match(type='LOG_ENTRY', blocking=True, timeout=5)
                if msg is None:
                    break
                msg_dict = msg.to_dict()
                log_entries.append(msg_dict)
                if msg_dict["last_log_num"] == msg_dict["id"]:
                    break

            for log_entry in log_entries:
                if not self.is_running:
                    break
                log_id = log_entry["id"]
                log_size = log_entry["size"]

                log_file_path = os.path.join(LOG_DIR, f"log_{log_id}.bin")
                if log_id not in self.downloaded_logs or os.path.getsize(log_file_path) == 0:
                    print(f"Downloading log {log_id}...")
                    success = self.download_log(log_id, log_size)
                    if success:
                        self.downloaded_logs.add(log_id)
                        self.save_downloaded_logs()
                        print(f"Log {log_id} successfully downloaded and saved.")

            time.sleep(5)

if __name__ == "__main__":
    if not ensure_dir_exists(LOG_DIR):
        print(f"Cannot access or create directory: {LOG_DIR}")
    else:
        download_logs = DownloadLogs('/dev/ttyACM0')
        download_logs.start()