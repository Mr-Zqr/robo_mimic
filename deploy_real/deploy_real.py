import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from common.path_config import PROJECT_ROOT
from common.ctrlcomp import *
from common.utils import FSMStateName
from FSM.FSM import *
from typing import Union
import numpy as np
import time
import os
import yaml

from unitree_sdk2py.core.channel import ChannelPublisher
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_, unitree_hg_msg_dds__LowState_
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_, unitree_go_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_ as LowCmdHG
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_ as LowCmdGo
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_ as LowStateHG
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_ as LowStateGo
from unitree_sdk2py.utils.crc import CRC

from common.command_helper import create_damping_cmd, create_zero_cmd, init_cmd_hg, init_cmd_go, MotorMode
from common.rotation_helper import get_gravity_orientation_real, transform_imu_data
from common.remote_controller import RemoteController, KeyMap
from common.joystick import Keyboard, KeyboardButton

from config import Config
from common.deploy_logger import DeployLogger


class Controller:
    def __init__(self, config: Config):
        self.config = config
        self.remote_controller = RemoteController()
        print("Remote controller initialized successfully!")
        print("No joystick detected, switching to keyboard control...")
        print("=" * 60)
        print("🎮 KEYBOARD CONTROL MODE ACTIVATED")
        print("=" * 60)
        print("📌 IMPORTANT: A separate control window will open!")
        print("   Focus on the 'Robot Keyboard Controller' window for input")
        print("   (NOT the MuJoCo window - it has conflicting shortcuts)")
        print("")
        print("🎯 Controls:")
        print("   WASD - Move robot")
        print("   Shift+Arrows - Rotate")
        print("   J(A), K(B), U(X), I(Y) - Action buttons")
        print("   Q(L1), E(R1) - Shoulder buttons")
        print("   Space(START), Esc(EXIT)")
        print("=" * 60)
        self.remote_controller = Keyboard()
        self.button_enum = KeyboardButton

        self.num_joints = config.num_joints
        self.control_dt = config.control_dt
        
        
        self.low_cmd = unitree_hg_msg_dds__LowCmd_()
        self.low_state = unitree_hg_msg_dds__LowState_()
        self.mode_pr_ = MotorMode.PR
        self.mode_machine_ = 0
        self.lowcmd_publisher_ = ChannelPublisher(config.lowcmd_topic, LowCmdHG)
        self.lowcmd_publisher_.Init()
        
        # inital connection
        self.lowstate_subscriber = ChannelSubscriber(config.lowstate_topic, LowStateHG)
        self.lowstate_subscriber.Init(self.LowStateHgHandler, 10)
        
        # self.wait_for_low_state()
        
        init_cmd_hg(self.low_cmd, self.mode_machine_, self.mode_pr_)
        
        self.policy_output_action = np.zeros(self.num_joints, dtype=np.float32)
        self.kps = np.zeros(self.num_joints, dtype=np.float32)
        self.kds = np.zeros(self.num_joints, dtype=np.float32)
        self.qj = np.zeros(self.num_joints, dtype=np.float32)
        self.dqj = np.zeros(self.num_joints, dtype=np.float32)
        self.quat = np.zeros(4, dtype=np.float32)
        self.ang_vel = np.zeros(3, dtype=np.float32)
        self.gravity_orientation = np.array([0,0,-1], dtype=np.float32)
        
        self.state_cmd = StateAndCmd(self.num_joints)
        self.policy_output = PolicyOutput(self.num_joints)
        self.FSM_controller = FSM(self.state_cmd, self.policy_output)
        
        # Initialize logger
        self.logger = DeployLogger()
        self.logging_active = False  # Start logging when entering active control modes
        self.previous_fsm_state = None  # Track FSM state changes
        
        self.running = True
        self.counter_over_time = 0

        
    def LowStateHgHandler(self, msg: LowStateHG):
        self.low_state = msg
        self.mode_machine_ = self.low_state.mode_machine
        # self.remote_controller.set(self.low_state.wireless_remote)

    def LowStateGoHandler(self, msg: LowStateGo):
        self.low_state = msg
        # self.remote_controller.set(self.low_state.wireless_remote)

    def send_cmd(self, cmd: Union[LowCmdGo, LowCmdHG]):
        cmd.crc = CRC().Crc(cmd)
        self.lowcmd_publisher_.Write(cmd)

    def wait_for_low_state(self):
        while self.low_state.tick == 0:
            time.sleep(self.config.control_dt)
        print("Successfully connected to the robot.")

    def zero_torque_state(self):
        print("Enter zero torque state.")
        print("Waiting for the start signal...")
        while self.remote_controller.button[KeyMap.start] != 1:
            create_zero_cmd(self.low_cmd)
            self.send_cmd(self.low_cmd)
            time.sleep(self.config.control_dt)
        
    def handle_logging(self):
        """Handle data logging based on FSM state"""
        current_fsm_state = self.FSM_controller.cur_policy.name
        current_fsm_state_str = self.FSM_controller.cur_policy.name_str
        
        # Check if we should start logging (entering active control modes)
        if (not self.logging_active and 
            current_fsm_state != FSMStateName.PASSIVE and 
            current_fsm_state != FSMStateName.FIXEDPOSE and
            current_fsm_state != FSMStateName.INVALID):
            
            print(f"🔴 Starting data logging - FSM State: {current_fsm_state_str}")
            self.logging_active = True
            self.logger = DeployLogger()  # Reset logger for new session
            
        # Check if we should stop logging and save (entering PASSIVE mode)
        elif (self.logging_active and 
              current_fsm_state == FSMStateName.PASSIVE and 
              self.previous_fsm_state != FSMStateName.PASSIVE):
            
            print(f"🟢 Stopping data logging - Saving to file (FSM State: {current_fsm_state_str})")
            self.save_current_log()
            self.logging_active = False
            
        # Record data if logging is active
        if self.logging_active:
            self.record_control_data()
            
        self.previous_fsm_state = current_fsm_state

    def record_control_data(self):
        """Record current control cycle data"""
        timestamp = time.time()
        
        # Record timestamp
        self.logger.record("timestamp", timestamp)
        
        # Record actual joint positions
        for i in range(self.num_joints):
            self.logger.record(f"actual_q_{i}", self.qj[i])
            self.logger.record(f"actual_dq_{i}", self.dqj[i])
        
        # Record target joint positions
        policy_output_action = self.policy_output.actions.copy()
        for i in range(self.num_joints):
            self.logger.record(f"target_q_{i}", policy_output_action[i])
            
        # Record control gains
        kps = self.policy_output.kps.copy()
        kds = self.policy_output.kds.copy()
        for i in range(self.num_joints):
            self.logger.record(f"kp_{i}", kps[i])
            self.logger.record(f"kd_{i}", kds[i])
            
        # Record velocity commands
        self.logger.record("vel_cmd_x", self.state_cmd.vel_cmd[0])
        self.logger.record("vel_cmd_y", self.state_cmd.vel_cmd[1])  
        self.logger.record("vel_cmd_yaw", self.state_cmd.vel_cmd[2])
        
        # Record FSM state
        self.logger.record("fsm_state", self.FSM_controller.cur_policy.name_str)
        self.logger.record("fsm_state_enum", str(self.FSM_controller.cur_policy.name))
        
        # Record IMU data
        self.logger.record("gravity_ori_x", self.state_cmd.gravity_ori[0])
        self.logger.record("gravity_ori_y", self.state_cmd.gravity_ori[1])
        self.logger.record("gravity_ori_z", self.state_cmd.gravity_ori[2])
        
        # Record angular velocity
        for i in range(3):
            self.logger.record(f"ang_vel_{i}", self.state_cmd.ang_vel[0][i])

    def save_current_log(self):
        """Save current log data to CSV file"""
        if len(self.logger.data) > 0:
            try:
                self.logger.save_to_csv()
                print("📊 Log data saved successfully!")
            except Exception as e:
                print(f"❌ Error saving log: {e}")
        else:
            print("⚠️  No data to save")

    def run(self):
        try:
            # if(self.counter_over_time >= config.error_over_time):
            #     raise ValueError("counter_over_time >= error_over_time")
            
            loop_start_time = time.time()
            self.remote_controller.update()
            # if self.remote_controller.is_button_pressed(KeyMap.F1):
            #     self.state_cmd.skill_cmd = FSMCommand.PASSIVE
            # if self.remote_controller.is_button_pressed(KeyMap.start):
            #     self.state_cmd.skill_cmd = FSMCommand.POS_RESET
            # if self.remote_controller.is_button_pressed(KeyMap.A) and self.remote_controller.is_button_pressed(KeyMap.R1):
            #     self.state_cmd.skill_cmd = FSMCommand.LOCO
            # if self.remote_controller.is_button_pressed(KeyMap.X) and self.remote_controller.is_button_pressed(KeyMap.R1):
            #     self.state_cmd.skill_cmd = FSMCommand.SKILL_1
            # if self.remote_controller.is_button_pressed(KeyMap.Y) and self.remote_controller.is_button_pressed(KeyMap.R1):
            #     self.state_cmd.skill_cmd = FSMCommand.SKILL_2
            if self.remote_controller.is_button_released(self.button_enum.L3):
                self.state_cmd.skill_cmd = FSMCommand.PASSIVE
            if self.remote_controller.is_button_released(self.button_enum.START):
                self.state_cmd.skill_cmd = FSMCommand.POS_RESET
            if self.remote_controller.is_button_released(self.button_enum.A) and self.remote_controller.is_button_pressed(self.button_enum.R1):
                self.state_cmd.skill_cmd = FSMCommand.LOCO
            if self.remote_controller.is_button_released(self.button_enum.X) and self.remote_controller.is_button_pressed(self.button_enum.R1):
                self.state_cmd.skill_cmd = FSMCommand.SKILL_1
            if self.remote_controller.is_button_released(self.button_enum.Y) and self.remote_controller.is_button_pressed(self.button_enum.R1):
                self.state_cmd.skill_cmd = FSMCommand.SKILL_2
            if self.remote_controller.is_button_released(self.button_enum.B) and self.remote_controller.is_button_pressed(self.button_enum.R1):
                self.state_cmd.skill_cmd = FSMCommand.SKILL_3
            if self.remote_controller.is_button_released(self.button_enum.Y) and self.remote_controller.is_button_pressed(self.button_enum.L1):
                self.state_cmd.skill_cmd = FSMCommand.SKILL_4
            # if self.remote_controller.is_button_pressed(KeyMap.B) and self.remote_controller.is_button_pressed(KeyMap.R1):
            #     self.state_cmd.skill_cmd = FSMCommand.SKILL_3
            # if self.remote_controller.is_button_pressed(KeyMap.Y) and self.remote_controller.is_button_pressed(KeyMap.L1):
            #     self.state_cmd.skill_cmd = FSMCommand.SKILL_4
            
            # self.state_cmd.vel_cmd[0] =  self.remote_controller.ly
            # self.state_cmd.vel_cmd[1] =  self.remote_controller.lx * -1
            # self.state_cmd.vel_cmd[2] =  self.remote_controller.rx * -1
            self.state_cmd.vel_cmd[0] = -self.remote_controller.get_axis_value(1)
            self.state_cmd.vel_cmd[1] = -self.remote_controller.get_axis_value(0)
            self.state_cmd.vel_cmd[2] = -self.remote_controller.get_axis_value(3)

            for i in range(self.num_joints):
                self.qj[i] = self.low_state.motor_state[i].q
                self.dqj[i] = self.low_state.motor_state[i].dq

            # imu_state quaternion: w, x, y, z
            quat = self.low_state.imu_state.quaternion
            ang_vel = np.array([self.low_state.imu_state.gyroscope], dtype=np.float32)
            
            gravity_orientation = get_gravity_orientation_real(quat)
            
            self.state_cmd.q = self.qj.copy()
            self.state_cmd.dq = self.dqj.copy()
            self.state_cmd.gravity_ori = gravity_orientation.copy()
            self.state_cmd.ang_vel = ang_vel.copy()
            
            self.FSM_controller.run()
            policy_output_action = self.policy_output.actions.copy()
            kps = self.policy_output.kps.copy()
            kds = self.policy_output.kds.copy()
            
            # Handle data logging
            self.handle_logging()
            
            # Build low cmd
            for i in range(self.num_joints):
                self.low_cmd.motor_cmd[i].q = policy_output_action[i]
                self.low_cmd.motor_cmd[i].qd = 0
                self.low_cmd.motor_cmd[i].kp = kps[i]
                self.low_cmd.motor_cmd[i].kd = kds[i]
                self.low_cmd.motor_cmd[i].tau = 0
                
            # send the command
            # create_damping_cmd(controller.low_cmd) # only for debug
            self.send_cmd(self.low_cmd)
            
            self.handle_logging()  # Manage logging based on FSM state
            
            loop_end_time = time.time()
            delta_time = loop_end_time - loop_start_time
            if(delta_time < self.control_dt):
                time.sleep(self.control_dt - delta_time)
                self.counter_over_time = 0
            else:
                print("control loop over time.")
                self.counter_over_time += 1
            pass
        except ValueError as e:
            print(str(e))
            pass
        
        pass
        
        
if __name__ == "__main__":
    config = Config()
    # Initialize DDS communication
    ChannelFactoryInitialize(1, "lo")
    
    controller = Controller(config)
    
    while True:
        try:
            controller.run()
            # Press the select key to exit
            if controller.remote_controller.is_button_pressed(KeyMap.select):
                break
        except KeyboardInterrupt:
            break
    
    # Save any remaining log data before exit
    if controller.logging_active:
        print("💾 Saving log data before exit...")
        controller.save_current_log()
    
    create_damping_cmd(controller.low_cmd)
    controller.send_cmd(controller.low_cmd)
    print("Exit")
