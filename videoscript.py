import cv2
import flask
from flask import Flask, Response
from datetime import datetime
import threading
import queue
import signal
import sys

app = Flask(__name__)

# Queue to hold frames to be served
frame_queue = queue.Queue(maxsize=1)

# Global variable to hold the camera instance
camera = None

def video_capture_thread():
    global camera
    camera = cv2.VideoCapture(0)
    
    # Check if the camera opened successfully
    if not camera.isOpened():
        print("Error: Unable to access the camera.")
        return

    # Generate a timestamped filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'/home/cbai/Rpanion-server/recorded_streams/output_{timestamp}.avi'

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            out.write(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            if not frame_queue.full():
                frame_queue.put(frame)
    
    camera.release()
    out.release()

@app.route('/video_feeed')
def video_feed():
    def generate_frames():
        while True:
            if not frame_queue.empty():
                frame = frame_queue.get()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def cleanup(signal_received, frame):
    print("SIGINT or CTRL-C detected. Cleaning up...")
    if camera is not None:
        camera.release()
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handler for cleanup on interruption
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Start the video capture thread
    capture_thread = threading.Thread(target=video_capture_thread, daemon=True)
    capture_thread.start()
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=8080)
