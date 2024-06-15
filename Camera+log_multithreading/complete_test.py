import os
import pickle
import json
import requests
import asyncio
import websockets
from pymavlink import mavutil

# Constants
LOG_DIR = "/home/alan/LIVE_LOGS/LOG_FILES"
TRACKING_FILE = os.path.join(LOG_DIR, "downloaded_logs.pkl")

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

def download_log(master, log_id, log_size):
    offset = 0
    count = 90  # 90 bytes per LOG_DATA message
    log_file_path = os.path.join(LOG_DIR, f"log_{log_id}.bin")

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
                    byte_data = bytes(data)
                    file.write(byte_data)
                    offset += len(data)

                if offset >= log_size:
                    print(f"Log {log_id} download complete.")
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

async def main(master):
    # Load the set of downloaded logs
    downloaded_logs = load_downloaded_logs()

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

if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Run the main function with the master instance passed from the main script
    master = None  # Initialize master
#     master = mavutil.mavlink_connection('/dev/ttyACM0', baud=115200)
#     asyncio.run(main(master))
    asyncio.get_event_loop().run_until_complete(main(master))