import os
import pickle
import time
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
VIDEO_DIR = "/home/cbai/Rpanion-server/recorded_streams"
UPLOAD_TRACKING_FILE = os.path.join(VIDEO_DIR, "uploaded_videos.pkl")
LOG_FILE = os.path.join(VIDEO_DIR, "upload_logs.log")

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(LOG_FILE),
                        logging.StreamHandler()
                    ])

# Helper functions for log tracking
def load_uploaded_logs():
    if os.path.exists(UPLOAD_TRACKING_FILE):
        with open(UPLOAD_TRACKING_FILE, 'rb') as f:
            return pickle.load(f)
    return set()

def save_uploaded_logs(uploaded_logs):
    with open(UPLOAD_TRACKING_FILE, 'wb') as f:
        pickle.dump(uploaded_logs, f)

# Function to upload video data with retry mechanism
def upload_video(filepath):
    url = 'https://cbweb.onrender.com/api/dronedata/'  # Replace with your actual API endpoint
    payload = {
        'droneid': 'ddh123jk',  # Replace with necessary fields
        'time': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    session = requests.Session()
    
    # Check the version of urllib3 and set up the retry strategy accordingly
    try:
        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
    except TypeError:
        # For older versions of urllib3
        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["POST"]
        )
    
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    
    try:
        with open(filepath, 'rb') as file:
            files = {'FileField': file}  # Key should match the API's expected field name
            response = session.post(url, data=payload, files=files)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            logging.info(f"Status Code: {response.status_code}")
            logging.info(f"Response Text: {response.text}")
            return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return False
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return False

def main():
    uploaded_logs = load_uploaded_logs()
    while True:
        for filename in os.listdir(VIDEO_DIR):
            if filename.endswith('.avi'):
                video_id = os.path.splitext(filename)[0]
                if video_id not in uploaded_logs:
                    video_file_path = os.path.join(VIDEO_DIR, filename)
                    logging.info(f"Uploading video {filename}...")
                    success = upload_video(video_file_path)
                    if success:
                        uploaded_logs.add(video_id)
                        save_uploaded_logs(uploaded_logs)
                        logging.info(f"Video {filename} successfully uploaded and tracked.")
                    else:
                        logging.error(f"Failed to upload video {filename}, will retry in the next iteration.")
        
        # Sleep for a while before the next upload attempt
        time.sleep(60)

# Entry point for the script
if __name__ == "__main__":
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)
    main()