import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from common.path_config import PROJECT_ROOT

import time
import mujoco.viewer
import mujoco
import numpy as np
import yaml
import os
from common.ctrlcomp import *
from FSM.FSM import *
from common.utils import get_gravity_orientation
from common.joystick import JoyStick, JoystickButton, Keyboard, KeyboardButton



def pd_control(target_q, q, kp, target_dq, dq, kd):
    """Calculates torques from position commands"""
    return (target_q - q) * kp + (target_dq - dq) * kd

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mujoco_yaml_path = os.path.join(current_dir, "config", "mujoco.yaml")
    with open(mujoco_yaml_path, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        xml_path = os.path.join(PROJECT_ROOT, config["xml_path"])
        simulation_dt = config["simulation_dt"]
        control_decimation = config["control_decimation"]
        
    m = mujoco.MjModel.from_xml_path(xml_path)
    d = mujoco.MjData(m)
    m.opt.timestep = simulation_dt
    mj_per_step_duration = simulation_dt * control_decimation
    num_joints = m.nu
    policy_output_action = np.zeros(num_joints, dtype=np.float32)
    kps = np.zeros(num_joints, dtype=np.float32)
    kds = np.zeros(num_joints, dtype=np.float32)
    sim_counter = 0
    
    state_cmd = StateAndCmd(num_joints)
    policy_output = PolicyOutput(num_joints)
    FSM_controller = FSM(state_cmd, policy_output)
    
    # Try to initialize joystick first, fallback to keyboard if no joystick is connected
    try:
        controller = JoyStick()
        button_enum = JoystickButton
        print("Joystick controller initialized successfully!")
    except RuntimeError:
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
        controller = Keyboard()
        button_enum = KeyboardButton
        
    Running = True
    with mujoco.viewer.launch_passive(m, d) as viewer:
        sim_start_time = time.time()
        while viewer.is_running() and Running:
            try:
                if(controller.is_button_pressed(button_enum.SELECT)):
                    Running = False

                controller.update()
                if controller.is_button_released(button_enum.L3):
                    state_cmd.skill_cmd = FSMCommand.PASSIVE
                if controller.is_button_released(button_enum.START):
                    state_cmd.skill_cmd = FSMCommand.POS_RESET
                if controller.is_button_released(button_enum.A) and controller.is_button_pressed(button_enum.R1):
                    state_cmd.skill_cmd = FSMCommand.LOCO
                if controller.is_button_released(button_enum.X) and controller.is_button_pressed(button_enum.R1):
                    state_cmd.skill_cmd = FSMCommand.SKILL_1
                if controller.is_button_released(button_enum.Y) and controller.is_button_pressed(button_enum.R1):
                    state_cmd.skill_cmd = FSMCommand.SKILL_2
                if controller.is_button_released(button_enum.B) and controller.is_button_pressed(button_enum.R1):
                    state_cmd.skill_cmd = FSMCommand.SKILL_3
                if controller.is_button_released(button_enum.Y) and controller.is_button_pressed(button_enum.L1):
                    state_cmd.skill_cmd = FSMCommand.SKILL_4
                
                state_cmd.vel_cmd[0] = -controller.get_axis_value(1)
                state_cmd.vel_cmd[1] = -controller.get_axis_value(0)
                state_cmd.vel_cmd[2] = -controller.get_axis_value(3)
                
                step_start = time.time()
                
                tau = pd_control(policy_output_action, d.qpos[7:], kps, np.zeros_like(kps), d.qvel[6:], kds)
                d.ctrl[:] = tau
                mujoco.mj_step(m, d)
                sim_counter += 1
                if sim_counter % control_decimation == 0:
                    
                    qj = d.qpos[7:]
                    dqj = d.qvel[6:]
                    quat = d.qpos[3:7]
                    
                    omega = d.qvel[3:6] 
                    gravity_orientation = get_gravity_orientation(quat)
                    
                    state_cmd.q = qj.copy()
                    state_cmd.dq = dqj.copy()
                    state_cmd.gravity_ori = gravity_orientation.copy()
                    state_cmd.ang_vel = omega.copy()
                    
                    FSM_controller.run()
                    policy_output_action = policy_output.actions.copy()
                    kps = policy_output.kps.copy()
                    kds = policy_output.kds.copy()
            except ValueError as e:
                print(str(e))
            
            viewer.sync()
            time_until_next_step = m.opt.timestep - (time.time() - step_start)
            if time_until_next_step > 0:
                time.sleep(time_until_next_step)
        