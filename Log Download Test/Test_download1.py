import os
import pickle
import json
import requests
import asyncio
import websockets
from pymavlink import mavutil
import time
import csv

# Constants
LOG_DIR = "/home/koustav/test_log_files/LOG_FILES"
TRACKING_FILE = os.path.join(LOG_DIR, "downloaded_logs.pkl")
BUFFER_SIZE = 4096  # Define a buffer size for writing to the file (4KB as an example)
CSV_FILE = os.path.join(LOG_DIR, "log_downloads.csv")

async def send_location_data(drone, lat, lon):
    uri = 'wss://cbsocket.onrender.com'
    async with websockets.connect(uri) as websocket:
        data = {"lat": lat, "lon": lon, "drone": drone}
        json_data = json.dumps(data)
        await websocket.send(json_data)
        print(f"Sent data: {data}")

def senddata(filepath):
    url = 'https://cbweb.onrender.com/api/dronedata/'
    payload = {
        'droneid': 'dfs',
        'time': '2024-12-12'
    }
    with open(filepath, 'rb') as file:
        files = {'FileField': file}
        response = requests.post(url, data=payload, files=files)
        print(response.status_code)
        print(response.text)

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

def log_to_csv(log_file, log_size, time_taken):
    with open(CSV_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([log_file, log_size / 1024, time_taken])

def download_log(master, log_id, log_size):
    offset = 0
    count = 0xFFFFFFFF  # 90 bytes per LOG_DATA message
    log_file_path = os.path.join(LOG_DIR, f"log_{log_id}.bin")
    buffer = bytearray()  # Initialize buffer
    
    start_time = time.time()  # Record the start time for download time calculation
    
    try:
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
                    buffer.extend(data)
                    
                    # Write buffer to file when buffer size is reached
                    if len(buffer) >= BUFFER_SIZE:
                        file.write(buffer)
                        buffer.clear()  # Clear buffer after writing
                    
                    offset += len(data)

                    # Calculate and display download speed
                    elapsed_time = time.time() - start_time
                    download_speed = offset / elapsed_time / 1024  # in KB/s
                    print(f"Downloading log {log_id}... {offset / 1024:.2f} KB / {log_size / 1024:.2f} KB at {download_speed:.2f} KB/s")
                
                if offset >= log_size:
                    # Write remaining buffer to file
                    if buffer:
                        file.write(buffer)
                        buffer.clear()  # Ensure buffer is cleared after writing

                    elapsed_time = time.time() - start_time  # Final download time
                    print(f"Log {log_id} download complete. Time taken: {elapsed_time:.2f} seconds")
                    log_to_csv(f"log_{log_id}.bin", log_size, elapsed_time)
                    senddata(log_file_path)
                    return True
    except Exception as e:
        print(f"An error occurred while downloading log {log_id}: {e}")

    # If download is incomplete or an error occurred, delete the partial file
    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    print(f"Incomplete log {log_id} removed.")
    return False

async def fetch_and_send_location(master):
    try:
        globalposition = master.recv_match(type=['GLOBAL_POSITION_INT', 'GLOBAL_POSITION'], blocking=True).to_dict()
        if globalposition is not None:
            if 'lat' in globalposition and 'lon' in globalposition:
                latitude = globalposition['lat'] / 1e7  
                longitude = globalposition['lon'] / 1e7 
                print("Latitude:", latitude)
                print("Longitude:", longitude)
                await send_location_data('ddh123jk', latitude, longitude)
    except Exception as error:
        print(error)

async def main():
    # Load the set of downloaded logs
    downloaded_logs = load_downloaded_logs()

    # Connect to the vehicle
    master = mavutil.mavlink_connection('/dev/ttyACM1', baud=115200)

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

    # Download logs that haven't been downloaded yet
    for log_entry in log_entries:
        log_id = log_entry["id"]
        log_size = log_entry["size"]
        
        if log_id not in downloaded_logs:
            print(f"Downloading log {log_id}...")
            if download_log(master, log_id, log_size):
                downloaded_logs.add(log_id)
                save_downloaded_logs(downloaded_logs)

    # After collecting all logs, only collect the last but one log on subsequent runs
    if len(log_entries) > 1:
        second_to_last_log = log_entries[-2]
        log_id = second_to_last_log["id"]
        log_size = second_to_last_log["size"]

        print(f"Downloading the second-to-last log {log_id}...")
        if download_log(master, log_id, log_size):
            downloaded_logs.add(log_id)
            save_downloaded_logs(downloaded_logs)

    # Close the connection
    master.close()

if __name__ == "__main__": 
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    initialize_csv()
    asyncio.run(main())
