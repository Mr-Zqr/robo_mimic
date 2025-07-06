# import numpy as np
# from collections import defaultdict
# from multiprocessing import Process, Value
import csv
import os
from datetime import datetime

class JointMap:
    L_hip_pitch = 0
    L_hip_roll = 1
    L_hip_yaw = 2
    L_knee = 3
    L_ankle_pitch = 4
    L_ankle_roll = 5
    R_hip_pitch = 6
    R_hip_roll = 7
    R_hip_yaw = 8
    R_knee = 9
    R_ankle_pitch = 10
    R_ankle_roll = 11
    Waist_yaw = 12
    Waist_roll = 13
    Waist_pitch = 14
    L_shoulder_pitch = 15
    L_shoulder_roll = 16
    L_shoulder_yaw = 17
    L_elbow = 18
    L_wrist_roll = 19
    L_wrist_pitch = 20
    L_wrist_yaw = 21
    R_shoulder_pitch = 22
    R_shoulder_roll = 23
    R_shoulder_yaw = 24
    R_elbow = 25
    R_wrist_roll = 26
    R_wrist_pitch = 27
    R_wrist_yaw = 28

class DeployLogger:
    def __init__(self):
        self.data = {}  # 用于存储数据的字典
        
        # 关节名称映射 (索引 -> 名称)
        self.joint_names = {
            0: "L_hip_pitch",
            1: "L_hip_roll", 
            2: "L_hip_yaw",
            3: "L_knee",
            4: "L_ankle_pitch",
            5: "L_ankle_roll",
            6: "R_hip_pitch",
            7: "R_hip_roll",
            8: "R_hip_yaw", 
            9: "R_knee",
            10: "R_ankle_pitch",
            11: "R_ankle_roll",
            12: "Waist_yaw",
            13: "Waist_roll",
            14: "Waist_pitch",
            15: "L_shoulder_pitch",
            16: "L_shoulder_roll",
            17: "L_shoulder_yaw",
            18: "L_elbow",
            19: "L_wrist_roll",
            20: "L_wrist_pitch",
            21: "L_wrist_yaw",
            22: "R_shoulder_pitch",
            23: "R_shoulder_roll",
            24: "R_shoulder_yaw",
            25: "R_elbow",
            26: "R_wrist_roll",
            27: "R_wrist_pitch",
            28: "R_wrist_yaw"
        }
        
    def get_joint_name(self, joint_index):
        """根据关节索引获取关节名称"""
        return self.joint_names.get(joint_index, f"joint_{joint_index}")
    
    def record_joint_data(self, joint_index, target_q, actual_q, actual_dq, kp, kd):
        """记录单个关节的所有数据"""
        joint_name = self.get_joint_name(joint_index)
        
        # 按照要求的命名格式：关节名称_数据类型
        self.record(f"{joint_name}_target", target_q)
        self.record(f"{joint_name}_actual", actual_q)
        self.record(f"{joint_name}_dq", actual_dq)
        self.record(f"{joint_name}_kp", kp)
        self.record(f"{joint_name}_kd", kd)

    def record(self, key, value):
        """记录数据，类似字典的方式"""
        if key not in self.data:
            self.data[key] = []  # 如果键不存在，初始化一个空列表
        self.data[key].append(value)

    def save_to_csv(self, filename=None):
        """将记录的数据保存为CSV文件"""
        if not self.data:
            print("⚠️  No data to save")
            return
            
        # 获取所有键（列名）
        columns = list(self.data.keys())
        # 获取最大行数（以最长的列表为准）
        max_rows = max(len(self.data[key]) for key in columns)
        # 创建log目录（如果不存在）
        if not os.path.exists('log'):
            os.makedirs('log')

        # 生成文件名（如果未提供）
        if filename is None:
            filename = datetime.now().strftime('log/robot_control_%Y%m%d_%H%M%S.csv')

        # 写入CSV文件
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            # 写入列名
            writer.writerow(columns)
            # 逐行写入数据
            for i in range(max_rows):
                row = [self.data[key][i] if i < len(self.data[key]) else "" for key in columns]
                writer.writerow(row)
                
        print(f"📊 Data saved to: {filename}")
        print(f"📈 Total records: {max_rows}")
        print(f"📋 Columns: {len(columns)}")
        
    def get_summary(self):
        """获取记录数据的摘要信息"""
        if not self.data:
            return "No data recorded"
            
        total_records = max(len(self.data[key]) for key in self.data.keys())
        columns = list(self.data.keys())
        
        return f"Records: {total_records}, Columns: {len(columns)}"