# import time
# from pymavlink import mavutil
# from picamera2 import Picamera2
# from picamera2.encoders import H264Encoder
# 
# # Initialize the PiCamera2
# picam2 = Picamera2()
# video_config = picam2.create_video_configuration()
# picam2.configure(video_config)
# encoder = H264Encoder(bitrate=10000000)
# 
# # Recording state
# is_recording = False
# output_directory = "/home/alan/Camera_test/recorded_videos/"
# 
# # Function to start recording
# def start_recording():
#     global is_recording
#     global output_filename
#     timestr = time.strftime("%d_%m_%Y-%H_%M_%S")
#     output_filename = output_directory + timestr + ".h264"
#     picam2.start_recording(encoder, output_filename)
#     is_recording = True
#     print("Recording started")
#     if is_recording==False: #remove?
#         stop_recording()
#         is_recording=False
# 
# # Function to stop recording
# def stop_recording():
#     global is_recording
#     if is_recording:
#         picam2.stop_recording()
#         is_recording = False
#         print("Recording stopped")
#     else:
#         print("No recording is currently active")
# 
# # Connect to the flight controller
# # print("Connecting to the flight controller...")
# # master = mavutil.mavlink_connection('/dev/ttyACM0', baud=115200)
# # if master:
# #     print("Connected to the flight controller.")
# 
# # Main loop
# try:
#     print("---WAIT FOR 5sec---")
#     while True:
#         # Wait for any MAVLink message
#         msg = master.recv_match(blocking=True)
#         if not msg:
#             time.sleep(0.1)  # Add a small delay before checking for messages again
#             continue
# 
#         if msg.get_type() == 'STATUSTEXT':
#             text = msg.text.strip()  # Remove leading/trailing whitespace
#             print("Received message:", text)
#             if text == "RC11: Camera Record Video HIGH":
#                 start_recording()
#             elif text == "RC11: Camera Record Video LOW":
#                 stop_recording()
# 
# except KeyboardInterrupt:
#     print("Exiting program")
# 
# # finally:
# #     if is_recording:
# #         stop_recording()
# #     picam2.close()
# #     connection.close()
# 
#



import time
from pymavlink import mavutil
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder

# Initialize the PiCamera2
picam2 = Picamera2()
video_config = picam2.create_video_configuration()
picam2.configure(video_config)
encoder = H264Encoder(bitrate=10000000)

# Recording state
is_recording = False
output_directory = "/home/alan/Camera_test/recorded_videos/"

# Function to start recording
def start_recording():
    global is_recording
    global output_filename
    timestr = time.strftime("%d_%m_%Y-%H_%M_%S")
    output_filename = output_directory + timestr + ".h264"
    picam2.start_recording(encoder, output_filename)
    is_recording = True
    print("Recording started")

# Function to stop recording
def stop_recording():
    global is_recording
    if is_recording:
        picam2.stop_recording()
        is_recording = False
        print("Recording stopped")
    else:
        print("No recording is currently active")

# Function to handle incoming messages and start/stop recording
def handle_message(master, message):
    if message.get_type() == 'STATUSTEXT':
        text = message.text.strip()  # Remove leading/trailing whitespace
        print("Received message:", text)
        if text == "RC11: Camera Record Video HIGH":
            start_recording()
        elif text == "RC11: Camera Record Video LOW":
            stop_recording()

# Main function to process MAVLink messages
def main(master):
    print("---WAIT FOR 5sec---")
    try:
        while True:
            # Wait for any MAVLink message
            msg = master.recv_match(blocking=True)
            if not msg:
                time.sleep(0.1)  # Add a small delay before checking for messages again
                continue

            handle_message(master, msg)

    except KeyboardInterrupt:
        print("Exiting program")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python camera_code.py <master_object>")
        sys.exit(1)

    # Convert the passed argument to master object
    master = eval(sys.argv[1])

    # Call the main function with the passed master object
    main(master)

