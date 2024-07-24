import os
import pickle
import time
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
LOG_DIR = "/media/koustav/Koustav/4G/5G/Logs/LOG_FILES"
TRACKING_FILE = os.path.join(LOG_DIR, "downloaded_logs.pkl")
UPLOAD_TRACKING_FILE = os.path.join(LOG_DIR, "uploaded_logs.pkl")
LOG_FILE = os.path.join(LOG_DIR, "upload_logs.log")

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(LOG_FILE),
                        logging.StreamHandler()
                    ])

# Helper functions for log tracking
def load_downloaded_logs():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'rb') as f:
            return pickle.load(f)
    return set()

def load_uploaded_logs():
    if os.path.exists(UPLOAD_TRACKING_FILE):
        with open(UPLOAD_TRACKING_FILE, 'rb') as f:
            return pickle.load(f)
    return set()

def save_uploaded_logs(uploaded_logs):
    with open(UPLOAD_TRACKING_FILE, 'wb') as f:
        pickle.dump(uploaded_logs, f)

# Function to send log data with retry mechanism
def senddata(filepath):
    url = 'https://cbweb.onrender.com/api/dronedata/'
    payload = {
        'droneid': 'ddh123jk',
        'time': '2024-12-12'
    }
    
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    
    try:
        with open(filepath, 'rb') as file:
            files = {'FileField': file}
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
        downloaded_logs = load_downloaded_logs()
        
        for log_id in downloaded_logs:
            if log_id not in uploaded_logs:
                log_file_path = os.path.join(LOG_DIR, f"log_{log_id}.bin")
                logging.info(f"Uploading log {log_id}...")
                success = senddata(log_file_path)
                if success:
                    uploaded_logs.add(log_id)
                    save_uploaded_logs(uploaded_logs)
                    logging.info(f"Log {log_id} successfully uploaded.")
                else:
                    logging.error(f"Failed to upload log {log_id}, will retry.")

        # Sleep for a while before the next upload attempt
        time.sleep(60)

# Entry point for the script
if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    main()


