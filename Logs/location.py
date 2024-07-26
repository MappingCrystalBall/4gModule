#!/usr/bin/env python3

import time
import asyncio
import json
import websockets
from pymavlink import mavutil

# Function to send location data via WebSocket
async def send_location_data(drone, lat, lon):
    uri = 'wss://cbsocket.onrender.com'
    async with websockets.connect(uri) as websocket:
        data = {"lat": lat, "lon": lon, "drone": drone}
        json_data = json.dumps(data)
        await websocket.send(json_data)
        print(f"Sent data: {data}")

# Function to fetch and send location data (asynchronous)
async def fetch_and_send_location(master):
    try:
        globalposition = master.recv_match(type=['GLOBAL_POSITION_INT', 'GLOBAL_POSITION'], blocking=True).to_dict()
        if globalposition is not None:
            if 'lat' in globalposition and 'lon' in globalposition:
                latitude = globalposition['lat'] / 1e7  
                longitude = globalposition['lon'] / 1e7 
                print(f"Location data: Latitude: {latitude}, Longitude: {longitude}")
                await send_location_data('ddh123jk', latitude, longitude)
    except Exception as error:
        print(f"Error fetching or sending location: {error}")

# Main function
def main():
    # Connection string for the vehicle
    connection_string = '/dev/ttyACM0'  # Adjust this as needed

    # Connect to the vehicle
    master = mavutil.mavlink_connection(connection_string, baud=9600)

    # Request a data stream
    master.mav.request_data_stream_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_POSITION,
        1, 1
    )

    print("*** LOCATION TRACKING STARTED ***")
    print("Connected to the vehicle. Starting location data transmission.")

    while True:
        # Run the asynchronous function in the event loop
        asyncio.run(fetch_and_send_location(master))
        # Sleep for a short while before checking again
        time.sleep(0.5)

# Entry point for the script
if __name__ == "__main__":
    main()