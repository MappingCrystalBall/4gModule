import time
from pymavlink import mavutil
from downloadlogs import DownloadLogs

class ArmChecker:
    def __init__(self, connection_string):
        self.master = mavutil.mavlink_connection(connection_string, baud=9600)
        self.download_logs = DownloadLogs(connection_string)
        # Wait for the first heartbeat 
        #   This sets the system and component ID of remote system for the link
        self.master.wait_heartbeat()
        print("Heartbeat from system (system %u component %u)" % 
              (self.master.target_system, self.master.target_component))

    def check_arm_status(self):
        self.master.mav.command_long_send(
            self.master.target_system, self.master.target_component,
            mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE, 0,
            mavutil.mavlink.MAVLINK_MSG_ID_HEARTBEAT, 0, 0, 0, 0, 0, 0
        )

        msg = self.master.recv_match(type='HEARTBEAT', blocking=True, timeout=5)
        if msg is not None:
            armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
            return armed
        return False

    def run(self):
        while True:
            try:
                is_armed = self.check_arm_status()
                if is_armed:
                    self.download_logs.stop()
                    print("Drone is armed. Stopped log download.")
                else:
                    self.download_logs.start()
                    print("Drone is disarmed. Started log download.")
                time.sleep(5)
            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(5)

if __name__ == "__main__":
    arm_checker = ArmChecker('/dev/ttyACM0')
    arm_checker.run()