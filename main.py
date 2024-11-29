import os
import pickle
import asyncio
from pymavlink import mavutil
from log_down import download_log as log_down_download_log  # Import the download_log function
from log_down import senddata, fetch_and_send_location
 
# Constants
LOG_DIR = "/home/alan/4G/Logs/LOG_FILES"
TRACKING_FILE = os.path.join(LOG_DIR, "downloaded_logs.pkl")
 
def load_downloaded_logs():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'rb') as f:
            return pickle.load(f)
    return set()
 
def save_downloaded_logs(downloaded_logs):
    with open(TRACKING_FILE, 'wb') as f:
        pickle.dump(downloaded_logs, f)
 
async def send_location_data_continuously(master):
    while True:
        globalposition = master.recv_match(type=['GLOBAL_POSITION_INT', 'GLOBAL_POSITION'], blocking=True).to_dict()
        if globalposition is not None:
            if 'lat' in globalposition and 'lon' in globalposition:
                latitude = globalposition['lat'] / 1e7
                longitude = globalposition['lon'] / 1e7
                print("Latitude:", latitude)
                print("Longitude:", longitude)
                await fetch_and_send_location(master)
        await asyncio.sleep(1)
 
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
 
    location_task = None
 
    while True:
        # Check if the drone is armed
        master.mav.command_long_send(
            master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE, 0,
            mavutil.mavlink.MAVLINK_MSG_ID_HEARTBEAT, 0, 0, 0, 0, 0, 0
        )
 
        msg = master.recv_match(type='HEARTBEAT', blocking=True)
        if msg is not None:
            armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
            if armed:
                if location_task is None or location_task.done():
                    print("Drone is armed, sending location data.")
                    location_task = asyncio.create_task(send_location_data_continuously(master))
            else:
                if location_task is not None and not location_task.done():
                    print("Drone is disarmed, stopping location data.")
                    location_task.cancel()
                    location_task = None
 
                print("Drone is disarmed, proceeding with log download.")
 
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
                    msg = master.recv_match(type='LOG_ENTRY', blocking=True, timeout=5)
                    if msg is None:
                        break
                    msg_dict = msg.to_dict()
                    log_entries.append(msg_dict)
                    if msg_dict["last_log_num"] == msg_dict["id"]:
                        break
 
                # Download logs that haven't been downloaded yet or were downloaded incorrectly
                for log_entry in log_entries:
                    log_id = log_entry["id"]
                    log_size = log_entry["size"]
 
                    log_file_path = os.path.join(LOG_DIR, f"log_{log_id}.bin")
                    if log_id not in downloaded_logs or os.path.getsize(log_file_path) == 0:
                        print(f"Downloading log {log_id}...")
                        success = log_down_download_log(connection_string, log_id, log_size, LOG_DIR)
                        if success:
                            downloaded_logs.add(log_id)
                            save_downloaded_logs(downloaded_logs)
                            print(f"Log {log_id} successfully downloaded and saved.")
                            senddata(log_file_path)  # Send the log data to the cloud
                        else:
                            print(f"Failed to download log {log_id} correctly.")
 
                # Sleep for a while before checking again
                await asyncio.sleep(10)
 
    # Close the connection
    master.close()
 
if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    asyncio.run(main())