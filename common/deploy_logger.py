# import numpy as np
# from collections import defaultdict
# from multiprocessing import Process, Value
import csv
import os
from datetime import datetime
    
class DeployLogger:
    def __init__(self):
        self.data = {}  # 用于存储数据的字典

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