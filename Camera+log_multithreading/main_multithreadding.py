import os
import threading
import time
from pymavlink import mavutil
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder

# Import code 1 and code 2 as functions
from complete_test import main as code1_main
from camera_test5 import main as code2_main

# Define a global master variable
master = None
master_lock = threading.Lock()

# Function to initialize the master connection
def init_master():
    global master
    # Connect to the flight controller
    print("Connecting to the flight controller...")
#     master = mavutil.mavlink_connection('/dev/ttyACM0', baud=115200)
#     if master:
#         print("Connected to the FC!!!")
    with master_lock:
        master = mavutil.mavlink_connection('/dev/ttyACM0', baud=115200)
    print("Connected to the flight controller.")


# Function to run code 1
def run_code1():
#     global master
#     # Ensure master is initialized before running code 1
#     while master is None:
#         time.sleep(1)  # Wait for master initialization
#     code1_main(master)
    global master
    while True:
        with master_lock:
            if master:
                # Run code 1 logic
                print("Running code 1")
                code1_main(master)
                break
        time.sleep(1)

# Function to run code 2
def run_code2():
#     global master
#     # Ensure master is initialized before running code 2
#     while master is None:
#         time.sleep(1)  # Wait for master initialization
#     code2_main(master)
    global master
    while True:
        with master_lock:
            if master:
                # Run code 2 logic
                print("Running code 2")
                code2_main(master)
                break
        time.sleep(1)

if __name__ == "__main__":
    # Initialize master connection in a separate thread
    master_thread = threading.Thread(target=init_master)
    master_thread.start()

    # Run code 1 and code 2 concurrently in separate threads
    code1_thread = threading.Thread(target=run_code1)
    code2_thread = threading.Thread(target=run_code2)
    code1_thread.start()
    code2_thread.start()

    # Wait for all threads to finish
    master_thread.join()
    code1_thread.join()
    code2_thread.join()
