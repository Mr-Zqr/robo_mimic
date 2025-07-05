# 机器人控制日志记录功能

## 功能概述

在 `deploy_real.py` 中新增了自动日志记录功能，用于记录机器人控制过程中的关键数据。

## 日志记录的数据

### 基本信息
- **timestamp**: 时间戳
- **fsm_state**: 当前FSM状态（字符串）
- **fsm_state_enum**: 当前FSM状态（枚举值）

### 关节控制数据
对于每个关节 i (0到28)：
- **actual_q_i**: 实际关节位置
- **actual_dq_i**: 实际关节速度
- **target_q_i**: 目标关节位置
- **kp_i**: 位置增益
- **kd_i**: 速度增益

### 运动控制命令
- **vel_cmd_x**: X方向速度命令
- **vel_cmd_y**: Y方向速度命令
- **vel_cmd_yaw**: 偏航角速度命令

### IMU数据
- **gravity_ori_x/y/z**: 重力方向向量
- **ang_vel_0/1/2**: 角速度（3轴）

## 自动日志记录逻辑

### 开始记录
当机器人从以下状态切换到活跃控制状态时，自动开始记录：
- 从 `PASSIVE` 状态切换到运动控制状态
- 从 `FIXEDPOSE` 状态切换到技能执行状态
- 从 `INVALID` 状态切换到任何有效状态

### 停止记录并保存
当机器人切换回 `PASSIVE` 状态时，自动停止记录并保存日志文件。

### 程序退出保存
如果程序意外终止（Ctrl+C等），会在退出前保存当前记录的数据。

## 日志文件格式

### 文件命名
日志文件保存在 `log/` 目录下，命名格式为：
```
robot_control_YYYYMMDD_HHMMSS.csv
```

### 文件内容
- CSV格式，便于数据分析
- 第一行为列名
- 每行代表一个控制周期的数据

## 使用示例

### 控制台输出
```bash
🔴 Starting data logging - FSM State: locomode
🟢 Stopping data logging - Saving to file (FSM State: passive)
📊 Data saved to: log/robot_control_20250705_101952.csv
📈 Total records: 1247
📋 Columns: 156
```

### 手动触发保存
在程序运行时按 Ctrl+C 会触发：
```bash
💾 Saving log data before exit...
📊 Data saved to: log/robot_control_20250705_102134.csv
```

## 数据分析

### 读取日志文件
```python
import pandas as pd
import matplotlib.pyplot as plt

# 读取日志文件
df = pd.read_csv('log/robot_control_20250705_101952.csv')

# 分析关节位置跟踪
joint_id = 0
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df[f'actual_q_{joint_id}'], label='Actual')
plt.plot(df['timestamp'], df[f'target_q_{joint_id}'], label='Target')
plt.xlabel('Time (s)')
plt.ylabel('Joint Position (rad)')
plt.title(f'Joint {joint_id} Position Tracking')
plt.legend()
plt.grid(True)
plt.show()
```

### 计算跟踪误差
```python
# 计算所有关节的位置误差
num_joints = 29
tracking_errors = []

for i in range(num_joints):
    actual = df[f'actual_q_{i}']
    target = df[f'target_q_{i}']
    error = np.abs(actual - target)
    tracking_errors.append(error.mean())

print("Average tracking error per joint:")
for i, error in enumerate(tracking_errors):
    print(f"Joint {i}: {error:.4f} rad")
```

## 配置选项

### 修改记录频率
目前每个控制周期都记录数据。如需降低记录频率，可以在 `record_control_data()` 中添加计数器：

```python
def record_control_data(self):
    # 只记录每10个周期的数据
    if self.control_cycle_count % 10 != 0:
        return
    # ... 记录数据的代码
```

### 选择性记录
可以根据需要修改 `record_control_data()` 方法，只记录特定的数据：

```python
def record_control_data(self):
    # 只记录关键关节的数据
    important_joints = [0, 1, 2, 12, 13, 14]  # 例如：腿部关节
    for i in important_joints:
        self.logger.record(f"actual_q_{i}", self.qj[i])
        self.logger.record(f"target_q_{i}", self.policy_output.actions[i])
```

## 故障排除

### 日志文件过大
如果日志文件过大，可以：
1. 降低记录频率
2. 选择性记录重要数据
3. 定期清理旧的日志文件

### 磁盘空间不足
建议定期清理 `log/` 目录：
```bash
# 删除7天前的日志文件
find log/ -name "*.csv" -mtime +7 -delete
```

### 性能影响
日志记录对控制性能的影响很小，但如果发现控制周期超时，可以：
1. 减少记录的数据量
2. 使用后台线程进行日志写入

## 测试

运行测试脚本验证日志记录功能：
```bash
python test_logger.py
```

该脚本会生成模拟数据并保存到CSV文件中，用于验证日志记录功能是否正常工作。
