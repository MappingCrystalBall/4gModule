import os
import pickle
import asyncio
from pymavlink import mavutil
from log_down import download_log as log_down_download_log  # Import the download_log function
from log_down import senddata, fetch_and_send_location

# Constants
LOG_DIR = "/home/koustav/test_log_files/LOG_FILES"
TRACKING_FILE = os.path.join(LOG_DIR, "downloaded_logs.pkl")

def load_downloaded_logs():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'rb') as f:
            return pickle.load(f)
    return set()

def save_downloaded_logs(downloaded_logs):
    with open(TRACKING_FILE, 'wb') as f:
        pickle.dump(downloaded_logs, f)

def download_log(connection_string, log_id, log_size):
    log_down_download_log(connection_string, log_id, log_size, LOG_DIR)

async def main():
    # Load the set of downloaded logs
    downloaded_logs = load_downloaded_logs()

    # Connection string for the vehicle
    connection_string = '/dev/ttyACM0'

    # Connect to the vehicle
    master = mavutil.mavlink_connection(connection_string, baud=9600)

    master.mav.request_data_stream_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_POSITION,
        1, 1
    )

    await fetch_and_send_location(master)

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
            print(f"Downloading log {log_id}...")
            download_log(connection_string, log_id, log_size)
            downloaded_logs.add(log_id)
            save_downloaded_logs(downloaded_logs)

            # Check if the log download was successful
            log_file_path = os.path.join(LOG_DIR, f"log_{log_id}.bin")
            if os.path.exists(log_file_path):
                print(f"Log {log_id} successfully downloaded and saved.")
                senddata(log_file_path)  # Send the log data to the cloud
            else:
                print(f"Failed to download log {log_id}.")

if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    asyncio.run(main())
