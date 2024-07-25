#!/usr/bin/env python3

import time
from pymavlink import mavutil

class ArmChecker:
    def __init__(self, connection_string):
        self.master = mavutil.mavlink_connection(connection_string, baud=9600)
        self.last_arm_state = None
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

    def get_arm_status(self):
        try:
            is_armed = self.check_arm_status()
            if is_armed != self.last_arm_state:
                self.last_arm_state = is_armed
                return is_armed, True  # Return arm status and whether it changed
            return is_armed, False  # Return arm status and that it didn't change
        except Exception as e:
            print(f"An error occurred in ArmChecker: {e}")
            return None, False