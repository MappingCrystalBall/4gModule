import os
from flask import Flask, Response, render_template
from flask import Flask, render_template, jsonify, send_file, send_from_directory, request
import subprocess
import time
import shutil
import threading
import re
import requests
import RPi.GPIO as GPIO
from pymavlink import mavutil
app = Flask(__name__)

# Define the serial connection string (use the correct device path, e.g., /dev/ttyACM0)
connection_string = "/dev/ttyACM0"
baud_rate = "57600"

# Path to save logs
log_file_path = "/tmp/mavproxy_logs"

LOG_DIRECTORY = "/home/raspberry"

folder_path = "/mnt"

file_path ="/home/raspberry/EndUser"

pin1 = 13
pin2 = 15

# Global variable to store logs and MAVProxy process
log_data = {}
mavproxy_process = None

# Function to start MAVProxy and establish the connection
def start_mavproxy():
    global mavproxy_process
    if mavproxy_process is None or mavproxy_process.poll() is not None:  # Check if the process is dead
        try:
            # Start MAVProxy as a subprocess and pass the connection details
            mavproxy_process = subprocess.Popen(
   ["mavproxy.py", "--master", connection_string, "--baudrate", baud_rate,
                 "--out", "127.0.0.1:14450"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )

            # Allow time for the connection to be established
            time.sleep(5)
        except Exception as e:
            print(f"Error starting MAVProxy: {e}")





def fetch_logs():
    global log_data
    try:
        # Ensure MAVProxy is started
        start_mavproxy()

        # Send the 'log list' command to MAVProxy via its stdin
        mavproxy_process.stdin.write(b"log list\n")
        mavproxy_process.stdin.flush()

        # Allow time for MAVProxy to process the request and display the logs
        time.sleep(5)

        # Read the output from MAVProxy and filter the lines starting with "Log"
        stdout, stderr = mavproxy_process.communicate(timeout=10)
        if stdout:
            # Decode and filter lines that start with "Log"
            log_lines = [line for line in stdout.decode().splitlines() if line.startswith("Log")]

            # Store the filtered logs globally with unique IDs (e.g., sequence number)
            log_data = {i: line for i, line in enumerate(log_lines)}

        if stderr:
            print("MAVProxy Errors:\n", stderr.decode())

    except subprocess.TimeoutExpired:
        print("MAVProxy process timed out.")
    except Exception as e:
        print(f"Error occurred: {e}")

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')
def upload_and_cleanup_local_folder():
    """Uploads files from the local folder to the cloud and deletes them after upload."""
    try:
        # Loop through all files in the local folder
        for file in os.listdir(file_path):
            local_file_path = os.path.join(file_path, file)
            success, message = upload_log_to_cloud(local_file_path, file)
            if not success:
                print(f"Error uploading file {file}: {message}")
                return jsonify({"error": f"Failed to upload file {file}: {message}"}), 500
            else:
                print(f"File {file} uploaded successfully.")
            
                
        return True  # Return success after processing all files
    except Exception as e:
        print(f"Error occurred while uploading and cleaning up local folder: {e}")
        return False, str(e)

@app.route('/list_files', methods=['GET'])
def list_files():
    try:
        # Initialize GPIO pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin1, GPIO.IN)
        GPIO.setup(pin2, GPIO.OUT, initial=GPIO.LOW)

        # Check the state of pin1
        pin1_state = GPIO.input(pin1)
        if pin1_state == GPIO.HIGH:
            print(f"GPIO {pin1} state: {'HIGH' if pin1_state else 'LOW'}")
            print("Logging is active. Cannot list files.")
            return jsonify({"error": "Logging is active. Cannot list files."}), 400

        # Pin1 is LOW, proceed to list files
        print("Pin1 is LOW. Proceeding to list files.")
        GPIO.output(pin2, GPIO.HIGH)  # Indicate file access is active
        print("Pin2 set to HIGH. File access is active.")

        # Copy files from folder_path to file_path using shutil
        files = os.listdir(folder_path)
        for file in files:
            source_file_path = os.path.join(folder_path, file)
            destination_file_path = os.path.join(file_path, file)

            if os.path.isfile(source_file_path):
                try:
                    # Copy the file to the destination folder using shutil
                    shutil.copy(source_file_path, destination_file_path)
                    print(f"File {file} copied from {folder_path} to {file_path}")
                except Exception as e:
                    print(f"Error copying file {file}: {e}")
                    return jsonify({"error": f"Failed to copy file {file}: {e}"}), 500

        # Get the updated list of files in file_path
        files_in_file_path = os.listdir(file_path)
        refreshed_file_list = [f for f in files_in_file_path if os.path.isfile(os.path.join(file_path, f))]
        print(f"Refreshed file list in file_path: {refreshed_file_list}")

        # Start the upload process in a separate thread
        threading.Thread(target=upload_and_cleanup_local_folder, daemon=True).start()

        # Set pin2 to LOW to indicate file access is complete
        GPIO.output(pin2, GPIO.LOW)
        print("Pin2 set to LOW. File access is complete.")

        # Return the updated file list to the user
        response = jsonify({"files": refreshed_file_list})
        response.status_code = 200

        return response

    except Exception as e:
        print(f"Error occurred in list_files: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        GPIO.cleanup()



@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # Check if the file exists in the file_path
        file_path_to_download = os.path.join(file_path, filename)
        if not os.path.exists(file_path_to_download):
            return jsonify({"error": "File not found"}), 404

        # Return the file for download (directly from file_path)
        print(f"File {filename} ready for download.")
        
        response = send_from_directory(file_path, filename, as_attachment=True)

        return response

    except Exception as e:
        print(f"Error occurred in download_file: {e}")
        return jsonify({"error": str(e)}), 500

    
# Route to fetch logs in the background and return them as JSON
@app.route('/fetch_logs', methods=['GET'])
def get_logs():
    # Run the fetch_logs function in a separate thread so it doesn't block the main thread
    threading.Thread(target=fetch_logs).start()

    return jsonify({"status": "loading"})

baud_rate = "115200"  # Replace with your baud rate


def starttele():
    try:
        # Start MAVProxy as a subprocess and pass the connection details
        subprocess.Popen(
            ["mavproxy.py", "--master", connection_string, "--baudrate", baud_rate,
             "--out", "127.0.0.1:14450"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        # Allow time for the connection to be established
        time.sleep(5)
    except Exception as e:
        print(f"Error starting MAVProxy: {e}")


def stream_roll_values():
    """Generator function to stream roll values."""
    try:
        # Connect to the MAVProxy output
        master = mavutil.mavlink_connection('udp:127.0.0.1:14450')
        
        # Wait for a heartbeat to ensure connection is established
        master.wait_heartbeat()
        print("Connected to MAVProxy telemetry stream")
        
        while True:
            # Listen for ATTITUDE messages
            msg = master.recv_match(type='ATTITUDE', blocking=True)
            if msg:
                roll = msg.roll  # Roll data in radians

                # Convert radians to degrees
                roll_deg = roll * (180.0 / 3.14159)

                # Yield roll value as part of the response
                yield f"data: {roll_deg:.2f}°\n\n"

                # Small delay to avoid overwhelming the stream
                time.sleep(0.1)

    except Exception as e:
        yield f"Error: {e}\n\n"


@app.route('/tele', methods=['GET'])
def tele():
    # Start MAVProxy in a separate thread
    threading.Thread(target=starttele, daemon=True).start()
    
    # Stream roll values to the client
    return Response(stream_roll_values(), content_type='text/event-stream')

# Route to get the fetched logs (returns log list with unique IDs)
@app.route('/logs', methods=['GET'])
def logs():
    return jsonify({"logs": log_data})

def upload_log_to_cloud(filepath, log_id):
    try:
        url = 'https://cbweb.onrender.com/api/dronedata/'  # Replace with actual cloud endpoint
        payload = {
            'droneid': 'dfs',  # Replace with actual drone ID if necessary
            'time': time.strftime("%Y-%m-%d %H:%M:%S")  # Timestamp for when the log is being uploaded
        }

        # Open the file and prepare the data for uploading
        with open(filepath, 'rb') as file:
            files = {'FileField': file}  # Replace 'FileField' with the actual field name expected by the API
            response = requests.post(url, data=payload, files=files)

        # Check if the response status is successful (200 or 201 OK)
        if response.status_code in [200, 201]:
            print(f"Log {log_id} uploaded successfully.")
            return True, f"Log {log_id} uploaded successfully."
        else:
            print(f"Failed to upload log {log_id}. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, f"Failed to upload log {log_id}. Status Code: {response.status_code}"

    except requests.exceptions.RequestException as e:
        # Handle network-related or request errors
        print(f"Network error while uploading log {log_id}: {e}")
        return False, f"Network error while uploading log {log_id}: {e}"
    except Exception as e:
        # Handle any other general exceptions
        print(f"An exception occurred while uploading log {log_id}: {e}")
        return False, f"An exception occurred while uploading log {log_id}: {e}"

def download_log(log_id):
    global mavproxy_process
    try:
        # Kill the existing MAVProxy process if it's running
        if mavproxy_process and mavproxy_process.poll() is None:
            print("Terminating the existing MAVProxy process...")
            mavproxy_process.terminate()
            mavproxy_process.wait()  # Wait for the process to terminate
            time.sleep(1)  # Give it a moment to ensure it's fully stopped

        # Ensure MAVProxy is started
        start_mavproxy()

        # Send the 'log download' command to MAVProxy
        log_command = f"log download {log_id}\n"
        mavproxy_process.stdin.write(log_command.encode())
        mavproxy_process.stdin.flush()

        # Wait until the download is finished by continuously reading the output
        output_log = []
        while True:
            output = mavproxy_process.stdout.readline()
            if output == "" and mavproxy_process.poll() is not None:
                break

            if output:
                output_str = output.strip().decode()
                output_log.append(output_str)
                print(output_str)  # Print to console

                # Check if the download finished
                if "Finished downloading" in output_str:
                    log_filepath = os.path.join(LOG_DIRECTORY, f"log{log_id}.bin")
                    if os.path.exists(log_filepath):
                        print(f"Log {log_id} downloaded successfully at {log_filepath}.")
                        upload_log_to_cloud(log_filepath, log_id)
                        return True, f"Log {log_id} downloaded and uploaded successfully."
                    return True, f"Log {log_id} downloaded successfully."

            time.sleep(0.1)

        # Check for any errors in stderr
        stderr = mavproxy_process.stderr.read()
        if stderr:
            return False, f"Error occurred while downloading log {log_id}: {stderr}"

    except Exception as e:
        print(f"Error downloading log {log_id}: {e}")
        return False, f"Log download failed with error: {e}"

@app.route("/download_log/<int:log_id>", methods=["GET"])
def download(log_id):
    # Call the download function
    success, message = download_log(log_id)

    # Return JSON response
    return jsonify({"success": success, "message": message}), 200 if success else 500



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
