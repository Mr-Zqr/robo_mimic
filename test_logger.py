#!/usr/bin/env python3
"""
Test script for the logging functionality
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.absolute()))

from common.deploy_logger import DeployLogger
import numpy as np
import time

def test_logger():
    """Test the logger functionality with mock data"""
    print("🧪 Testing DeployLogger functionality...")
    
    # Create logger
    logger = DeployLogger()
    
    # Simulate some control cycles
    num_joints = 29  # Typical for humanoid robots
    num_cycles = 100
    
    print(f"📊 Simulating {num_cycles} control cycles with {num_joints} joints...")
    
    for cycle in range(num_cycles):
        # Simulate timestamp
        timestamp = time.time() + cycle * 0.02  # 50Hz control
        logger.record("timestamp", timestamp)
        
        # Simulate joint positions
        for i in range(num_joints):
            # Simulate actual joint positions (with some noise)
            actual_q = np.sin(cycle * 0.1 + i * 0.2) + np.random.normal(0, 0.01)
            actual_dq = np.cos(cycle * 0.1 + i * 0.2) + np.random.normal(0, 0.05)
            logger.record(f"actual_q_{i}", actual_q)
            logger.record(f"actual_dq_{i}", actual_dq)
            
            # Simulate target joint positions
            target_q = np.sin(cycle * 0.1 + i * 0.2)
            logger.record(f"target_q_{i}", target_q)
            
            # Simulate control gains
            kp = 50.0 + np.random.normal(0, 5.0)
            kd = 2.0 + np.random.normal(0, 0.2)
            logger.record(f"kp_{i}", kp)
            logger.record(f"kd_{i}", kd)
        
        # Simulate velocity commands
        logger.record("vel_cmd_x", np.sin(cycle * 0.05))
        logger.record("vel_cmd_y", np.cos(cycle * 0.05))
        logger.record("vel_cmd_yaw", np.sin(cycle * 0.03))
        
        # Simulate FSM state
        states = ["PASSIVE", "LOCO", "SKILL_1", "SKILL_2"]
        current_state = states[cycle % len(states)]
        logger.record("fsm_state", current_state)
        
        # Simulate IMU data
        logger.record("gravity_ori_x", np.sin(cycle * 0.02))
        logger.record("gravity_ori_y", np.cos(cycle * 0.02))
        logger.record("gravity_ori_z", -0.9 + np.random.normal(0, 0.1))
        
        # Simulate angular velocity
        for i in range(3):
            ang_vel = np.random.normal(0, 0.1)
            logger.record(f"ang_vel_{i}", ang_vel)
    
    # Display summary
    print(f"✅ Simulation complete!")
    print(f"📊 Summary: {logger.get_summary()}")
    
    # Save to CSV
    print("💾 Saving to CSV...")
    logger.save_to_csv()
    
    print("🎉 Test completed successfully!")

if __name__ == "__main__":
    test_logger()
