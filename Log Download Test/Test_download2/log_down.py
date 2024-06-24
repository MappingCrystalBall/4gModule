import os
import pickle
import time
import csv
import sys
from pymavlink import mavutil

LOG_DIR = "/home/koustav/test_log_files/LOG_FILES"
TRACKING_FILE = os.path.join(LOG_DIR, "downloaded_logs.pkl")
BUFFER_SIZE = 4096  # Define a buffer size for writing to the file (4KB as an example)
CSV_FILE = os.path.join(LOG_DIR, "log_downloads.csv")

def load_downloaded_logs():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'rb') as f:
            return pickle.load(f)
    return set()

def save_downloaded_logs(downloaded_logs):
    with open(TRACKING_FILE, 'wb') as f:
        pickle.dump(downloaded_logs, f)

def log_to_csv(log_file, log_size, time_taken):
    with open(CSV_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([log_file, log_size / 1024, time_taken])

def download_log(connection_string, log_id, log_size):
    offset = 0
    count = 0xFFFFFFFF  # 90 bytes per LOG_DATA message
    log_file_path = os.path.join(LOG_DIR, "log_{}.bin".format(log_id))
    buffer = bytearray()  # Initialize buffer
    
    start_time = time.time()  # Record the start time for download time calculation
    
    try:
        master = mavutil.mavlink_connection(connection_string, baud=57600)
        master.mav.request_data_stream_send(
            master.target_system, master.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_POSITION,
            1, 1
        )

        with open(log_file_path, "wb") as file:
            while offset < log_size:
                master.mav.log_request_data_send(
                    target_system=1,
                    target_component=0,
                    id=log_id,
                    ofs=offset,
                    count=count
                )
                
                msg = master.recv_match(type='LOG_DATA', blocking=True, timeout=5)
                if msg is not None and msg.get_type() == 'LOG_DATA':
                    data = msg.data
                    buffer.extend(data)  # Add data to buffer
                    
                    # Write buffer to file when buffer size is reached
                    if len(buffer) >= BUFFER_SIZE:
                        file.write(buffer)
                        buffer.clear()  # Clear buffer after writing
                    
                    offset += len(data)

                    # Calculate and display download speed
                    elapsed_time = time.time() - start_time
                    download_speed = offset / elapsed_time / 1024  # in KB/s
                    print("Downloading log {}... {:.2f} KB / {:.2f} KB at {:.2f} KB/s".format(log_id, offset / 1024, log_size / 1024, download_speed))
                
                if offset >= log_size:
                    # Write remaining buffer to file
                    if buffer:
                        file.write(buffer)
                        buffer.clear()  # Ensure buffer is cleared after writing

                    elapsed_time = time.time() - start_time  # Final download time
                    print("Log {} download complete. Time taken: {:.2f} seconds".format(log_id, elapsed_time))
                    log_to_csv("log_{}.bin".format(log_id), log_size, elapsed_time)
                    return True
    except Exception as e:
        print("An error occurred while downloading log {}: {}".format(log_id, e))
    finally:
        if 'master' in locals():
            master.close()  # Ensure the master connection is closed
        buffer.clear()  # Ensure the buffer is cleared

    # If download is incomplete or an error occurred, delete the partial file
    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    print("Incomplete log {} removed.".format(log_id))
    return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python log_down.py <connection_string> <log_id> <log_size>")
        sys.exit(1)

    connection_string = sys.argv[1]
    log_id = int(sys.argv[2])
    log_size = int(sys.argv[3])

    if download_log(connection_string, log_id, log_size):
        downloaded_logs = load_downloaded_logs()
        downloaded_logs.add(log_id)
        save_downloaded_logs(downloaded_logs)
        print("Log {} successfully downloaded and saved.".format(log_id))
