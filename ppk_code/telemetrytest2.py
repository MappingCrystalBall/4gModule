
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
import os
import subprocess

app = Flask(__name__)

# Define the serial connection string (use the correct device path, e.g., /dev/ttyACM0)
connection_string = "/dev/ttyACM0"
baud_rate = "57600"

# Path to save logs
log_file_path = "/tmp/mavproxy_logs"

LOG_DIRECTORY = "/home/cb/Documents/tt"

folder_path = "/mnt"

file_path ="/home/raspberry/EndUser"

pin1 = 20
pin2 = 21

# Global variable to store logs and MAVProxy process
log_data = {}
mavproxy_process = None

# Function to start MAVProxy and establish the connection
def start_mavproxy():
    print('MAVProxy initiated')
    global mavproxy_process

    # Kill any process holding the port
    kill_port(connection_string)  # Replace with your port, e.g., '/dev/ttyUSB0'

    try:
        mavproxy_process = subprocess.Popen(
            ["mavproxy.py", "--master", connection_string, "--baudrate", baud_rate,
             "--out", "0.0.0.0:14450"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        # Allow time for the connection to establish
        time.sleep(5)

    except Exception as e:
        print(f"Error starting MAVProxy: {e}")


def stop_mavproxy():
    """
    Terminates the MAVProxy process if it is running.
    """
    global mavproxy_process
    if mavproxy_process and mavproxy_process.poll() is None:  # Check if the process is running
        mavproxy_process.terminate()  # Gracefully terminate the process
        try:
            mavproxy_process.communicate(timeout=5)  # Allow it to clean up resources
        except subprocess.TimeoutExpired:
            mavproxy_process.kill()  # Force kill if it doesn't terminate in time
        mavproxy_process = None  

def kill_port(port_name):
    """
    Kills any process using the specified port.
    :param port_name: The name of the serial port (e.g., '/dev/ttyUSB0').
    """
    try:
        # Get the process ID(s) using the port
        result = subprocess.check_output(['lsof', port_name], text=True).splitlines()

        # Parse the output to extract PIDs
        for line in result[1:]:  # Skip the header line
            parts = line.split()
            if len(parts) > 1:
                pid = parts[1]  # Second column is the PID
                print(f"Killing process {pid} using port {port_name}")
                os.kill(int(pid), 9)  # Force kill the process

    except subprocess.CalledProcessError:
        print(f"No process found using {port_name}")
    except Exception as e:
        print(f"Error killing process: {e}")

def fetch_logs():
    """
    Fetches logs from MAVProxy by sending the 'log list' command.
    Ensures any existing logs are cleared before fetching new ones.
    If MAVProxy fails, it is forcefully terminated and restarted.
    """
    global log_data
    log_data = {}  # Clear existing logs

    def restart_mavproxy():
        """Forcefully kill MAVProxy if it's stuck and restart."""
        global mavproxy_process
        if mavproxy_process and mavproxy_process.poll() is None:  # If MAVProxy is running
            try:
                mavproxy_process.kill()  # Force kill the process
                mavproxy_process.communicate()  # Clean up resources
            except Exception as e:
                print(f"Error force-killing MAVProxy: {e}")
        start_mavproxy()

    try:
        # Stop MAVProxy if running
        stop_mavproxy()
        
        # Start MAVProxy
        start_mavproxy()

        # Send the 'log list' command to MAVProxy via its stdin
        mavproxy_process.stdin.write(b"log list\n")
        mavproxy_process.stdin.flush()

        # Allow time for MAVProxy to process the request and display the logs
        time.sleep(5)

        # Capture the output from MAVProxy
        stdout, stderr = mavproxy_process.communicate(timeout=10)

        if stdout:
            # Decode and filter lines that start with "Log"
            log_lines = [line for line in stdout.decode().splitlines() if line.startswith("Log")]

            # Store the filtered logs globally with unique IDs (e.g., sequence number)
            log_data = {i: line for i, line in enumerate(log_lines)}

            print("Fetched logs successfully.")
        
        if stderr:
            print("MAVProxy Errors:\n", stderr.decode())

    except subprocess.TimeoutExpired:
        print("MAVProxy process timed out. Restarting MAVProxy...")
        restart_mavproxy()  # Restart MAVProxy on timeout
    except Exception as e:
        print(f"Error occurred: {e}. Restarting MAVProxy...")
        restart_mavproxy()  # Restart MAVProxy on any other failure
    finally:
        # Ensure MAVProxy is stopped after fetching logs
        stop_mavproxy()

        # Confirm logs have been cleared if no logs were fetched
        if not log_data:
            print("No logs fetched. Log data cleared.")



# Route for the homepage
@app.route('/')
def index():
    start_mavproxy()
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
        GPIO.setup(pin1, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
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

        print(f"Pin2 initial state: {GPIO.input(pin2)}")

      
        # Copy files from folder_path to file_path using shutil
        files = os.listdir(folder_path)
        refreshed_file_list = []
        for file in files:
            source_file_path = os.path.join(folder_path, file)
            destination_file_path = os.path.join(file_path, file)

            print(f"Checking folder path: {folder_path}")


            if os.path.isfile(source_file_path):
                try:
                    # Copy the file to the destination folder using shutil
                    shutil.copy(source_file_path, destination_file_path)
                    print(f"File {file} copied from {folder_path} to {file_path}")
                    refreshed_file_list.append(file)
                except Exception as e:
                    print(f"Error copying file {file}: {e}")
                    return jsonify({"error": f"Failed to copy file {file}: {e}"}), 500

        # Get the updated list of files in file_path
        print(f"Refreshed file list in file_path: {refreshed_file_list}")

        # Set pin2 to LOW to indicate file access is complete
        GPIO.output(pin2, GPIO.LOW)
        print("Pin2 set to LOW. File access is complete.")

        # Return the updated file list to the user before starting uploads
        response = jsonify({"files": refreshed_file_list})
        response.status_code = 200

        # Start the upload process in a separate thread
        threading.Thread(target=upload_files_one_by_one, args=(refreshed_file_list,), daemon=True).start()

        return response

    except Exception as e:
        print(f"Error occurred in list_files: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        GPIO.cleanup()


def upload_files_one_by_one(file_list):
    """
    Uploads files one by one and cleans up after each upload.
    """
    try:
        for file in file_list:
            file_path = os.path.join(file_path, file)
            if os.path.isfile(file_path):
                try:
                    # Simulate file upload (replace this with your upload function)
                    upload_log_to_cloud(file_path)
                    print(f"File {file} uploaded successfully.")

                    # Optionally remove the file after upload
                    os.remove(file_path)
                    print(f"File {file} removed after upload.")
                except Exception as e:
                    print(f"Error uploading file {file}: {e}")
    except Exception as e:
        print(f"Error occurred during file upload process: {e}")


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

                # Yield roll value as part of the response
                yield f"data: {roll:.2f}°\n\n"

                # Small delay to avoid overwhelming the stream
                time.sleep(0.1)

    except Exception as e:
        yield f"Error: {e}\n\n"


@app.route('/location-data')
def location_data():
    """Stream location data."""
    def stream_location():
        try:
            master = mavutil.mavlink_connection('udp:127.0.0.1:14450')
            master.wait_heartbeat()
            print("Connected to MAVProxy telemetry stream")
            
            while True:
                msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
                if msg:
                    lat = msg.lat / 1e7
                    lng = msg.lon / 1e7
                    alt = msg.alt /1000
                    yield f"data: {{\"lat\": {lat}, \"lng\": {lng},\"alt\":{alt}}}\n\n"
                    time.sleep(0.5)
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

    return Response(stream_location(), content_type='text/event-stream')


@app.route('/tele', methods=['GET'])
def tele():
    # Start MAVProxy in a separate thread
    threading.Thread(target=starttele, daemon=True).start()
    
    # Stream location values to the client
    return Response(stream_roll_values(), content_type='text/event-stream')

@app.route('/location', methods=['GET'])
def location():
    # Start MAVProxy in a separate thread
    threading.Thread(target=starttele, daemon=True).start()

    # Stream location data using SSE with the correct MIME type
    return render_template ("map_page.html")
    #return Response(stream_location_values(), content_type='text/event-stream')

# Route to get the fetched logs (returns log list with unique IDs)
@app.route('/logs', methods=['GET'])
def logs():
    return jsonify({"logs": log_data})

def upload_log_to_cloud(filepath, log_id):
    try:
        url = 'http://35.173.243.132/api/dronedata/'  # Replace with actual cloud endpoint
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

# Global variable to track cancellation status
cancel_download = False

def download_log(log_id):
    global mavproxy_process, cancel_download
    try:
        # Kill the existing MAVProxy process if it's running
        if mavproxy_process and mavproxy_process.poll() is None:
            print("Terminating the existing MAVProxy process...")
            mavproxy_process.terminate()
            try:
                mavproxy_process.communicate(timeout=5)  # Gracefully terminate
            except subprocess.TimeoutExpired:
                mavproxy_process.kill()  # Force kill if necessary
            time.sleep(1)  # Ensure it's fully stopped

        # Ensure MAVProxy is started
        start_mavproxy()

        # Send the 'log download' command to MAVProxy
        log_command = f"log download {log_id}\n"
        mavproxy_process.stdin.write(log_command.encode())
        mavproxy_process.stdin.flush()

        # Path where the log file is expected to be downloaded
        log_filepath = os.path.join(LOG_DIRECTORY, f"log{log_id}.bin")

        # Continuously monitor the file size during the download
        previous_size = 0
        stable_counter = 0  # To ensure the file size stabilizes before concluding

        while True:
            # Check if the file exists
            if os.path.exists(log_filepath):
                current_size = os.path.getsize(log_filepath)
                print(f"Current log file size: {current_size} bytes")

                # Check if the file size has stabilized
                if current_size == previous_size:
                    stable_counter += 1
                else:
                    stable_counter = 0  # Reset the counter if file size changes

                if stable_counter > 10:  # Stable for 10 iterations (~1 second delay)
                    print(f"Log {log_id} downloaded successfully at {log_filepath}.")
                    
                    # Check if the download was canceled
                    if cancel_download:
                        # Delete the log file if the download was canceled
                        if os.path.exists(log_filepath):
                            os.remove(log_filepath)
                        print(f"Log download canceled. Log file removed from {LOG_DIRECTORY}.")
                        return False, "Log download was canceled and not uploaded."
                    
                    # Upload to cloud after successful download
                    upload_log_to_cloud(log_filepath, log_id)
                    return True, f"Log {log_id} downloaded and uploaded successfully."

                previous_size = current_size

            # Check if MAVProxy terminated unexpectedly
            if mavproxy_process.poll() is not None:
                print("MAVProxy process terminated unexpectedly.")
                break

            time.sleep(0.1)

        # Check for any errors in stderr
        stderr = mavproxy_process.stderr.read()
        if stderr:
            error_msg = stderr.decode().strip()
            print(f"Error from MAVProxy: {error_msg}")
            return False, f"Error occurred while downloading log {log_id}: {error_msg}"

    except Exception as e:
        print(f"Error downloading log {log_id}: {e}")
        return False, f"Log download failed with error: {e}"
    finally:
        # Stop MAVProxy after the operation
        if mavproxy_process and mavproxy_process.poll() is None:
            mavproxy_process.terminate()
            try:
                mavproxy_process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                mavproxy_process.kill()


@app.route('/cancel_log_download', methods=['POST'])
def cancel_log_download():
    global mavproxy_process, cancel_download
    if mavproxy_process:
        mavproxy_process.terminate()  # Stop the MAVProxy process
        cancel_download = True  # Mark the download as canceled
        return jsonify({"status": "stopped", "message": "Download canceled."})
    return jsonify({"status": "not running"})




@app.route("/download_log/<int:log_id>", methods=["GET"])
def download(log_id):
    # Call the download function
    success, message = download_log(log_id)

    # Return JSON response
    return jsonify({"success": success, "message": message}), 200 if success else 500



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
