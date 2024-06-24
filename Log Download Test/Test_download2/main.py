import os
import pickle
import subprocess
import sys
from pymavlink import mavutil

# Constants
LOG_DIR = "/home/koustav/test_log_files/LOG_FILES"
TRACKING_FILE = os.path.join(LOG_DIR, "downloaded_logs.pkl")
CSV_FILE = os.path.join(LOG_DIR, "log_downloads.csv")

def load_downloaded_logs():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'rb') as f:
            return pickle.load(f)
    return set()

def save_downloaded_logs(downloaded_logs):
    with open(TRACKING_FILE, 'wb') as f:
        pickle.dump(downloaded_logs, f)

def initialize_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Log File", "Size (KB)", "Time Taken (s)"])

def call_log_down_py(connection_string, log_id, log_size):
    subprocess.run([sys.executable, "log_down.py", connection_string, str(log_id), str(log_size)])

def main():
    # Load the set of downloaded logs
    downloaded_logs = load_downloaded_logs()

    # Connection string for the vehicle
    connection_string = '/dev/ttyACM0'

    # Connect to the vehicle
    master = mavutil.mavlink_connection(connection_string, baud=57600)
    master.mav.request_data_stream_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_POSITION,
        1, 1
    )

    # Request the list of logs
    master.mav.log_request_list_send(
        target_system=1,
        target_component=0,
        start=0,
        end=0xffff
    )

    # Get the list of logs
    log_entries = []
    while True:
        msg = master.recv_match(type='LOG_ENTRY', blocking=True)
        if msg is None:
            break
        msg_dict = msg.to_dict()
        log_entries.append(msg_dict)
        if msg_dict["last_log_num"] == msg_dict["id"]:
            break

    # Close the connection
    master.close()

    # Download logs that haven't been downloaded yet
    for log_entry in log_entries:
        log_id = log_entry["id"]
        log_size = log_entry["size"]
        
        if log_id not in downloaded_logs:
            print("Downloading log {}...".format(log_id))
            call_log_down_py(connection_string, log_id, log_size)
            downloaded_logs.add(log_id)
            save_downloaded_logs(downloaded_logs)

    # After collecting all logs, only collect the last but one log on subsequent runs
    if len(log_entries) > 1:
        second_to_last_log = log_entries[-2]
        log_id = second_to_last_log["id"]
        log_size = second_to_last_log["size"]

        print("Downloading the second-to-last log {}...".format(log_id))
        call_log_down_py(connection_string, log_id, log_size)
        downloaded_logs.add(log_id)
        save_downloaded_logs(downloaded_logs)

if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    initialize_csv()
    main()
