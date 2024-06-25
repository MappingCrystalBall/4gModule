from pymavlink import mavutil
import sys
import os
import time
import json
import requests
import asyncio
import websockets

def download_log(connection_string, log_id, log_size, log_dir):
    master = mavutil.mavlink_connection(connection_string, baud=9600)
    
    # Request the log
    master.mav.log_request_data_send(
        target_system=1,
        target_component=0,
        id=log_id,
        ofs=0,
        count=log_size
    )

    # Read the log
    log_file_path = os.path.join(log_dir, f"log_{log_id}.bin")
    start_time = time.time()
    bytes_downloaded = 0

    with open(log_file_path, 'wb') as f:
        while True:
            msg = master.recv_match(type='LOG_DATA', blocking=True, timeout=5)
            if msg is None:
                break
            data = bytes(msg.data)  # Convert list to bytes
            f.write(data)
            bytes_downloaded += len(data)
            elapsed_time = time.time() - start_time
            download_speed = bytes_downloaded / elapsed_time if elapsed_time > 0 else 0
            # Print the current status
            print(f"\rDownloading log {log_id}: {bytes_downloaded / 1024:.2f} KB of {log_size / 1024:.2f} KB "
                  f"({bytes_downloaded / log_size * 100:.2f}%) at {download_speed / 1024:.2f} KB/s", end='')

            if msg.ofs + len(msg.data) >= log_size:
                break

    elapsed_time = time.time() - start_time
    print(f"\nDownload of log {log_id} completed in {elapsed_time:.2f} seconds.")
    master.close()

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

async def send_location_data(drone, lat, lon):
    uri = 'wss://cbsocket.onrender.com'
    async with websockets.connect(uri) as websocket:
        data = {"lat": lat, "lon": lon, "drone": drone}
        json_data = json.dumps(data)
        await websocket.send(json_data)
        print(f"Sent data: {data}")

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

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python log_down.py <connection_string> <log_id> <log_size> <log_dir>")
        sys.exit(1)

    connection_string = sys.argv[1]
    log_id = int(sys.argv[2])
    log_size = int(sys.argv[3])
    log_dir = sys.argv[4]

    download_log(connection_string, log_id, log_size, log_dir)
