#!/usr/bin/env python3
"""
Sample data analysis script for robot control logs
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob

def analyze_latest_log():
    """分析最新的日志文件"""
    # 找到最新的日志文件
    log_files = glob.glob("log/robot_control_*.csv")
    if not log_files:
        print("❌ No log files found in log/ directory")
        return
    
    latest_log = max(log_files, key=os.path.getctime)
    print(f"📊 Analyzing: {latest_log}")
    
    # 读取数据
    df = pd.read_csv(latest_log)
    print(f"📈 Total records: {len(df)}")
    print(f"📋 Columns: {len(df.columns)}")
    
    # 基本统计信息
    print("\n📊 Basic Statistics:")
    print(f"   Duration: {df['timestamp'].max() - df['timestamp'].min():.2f} seconds")
    print(f"   Control frequency: {len(df) / (df['timestamp'].max() - df['timestamp'].min()):.1f} Hz")
    
    # FSM状态分析
    print("\n🔄 FSM State Analysis:")
    state_counts = df['fsm_state'].value_counts()
    for state, count in state_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   {state}: {count} cycles ({percentage:.1f}%)")
    
    # 关节跟踪误差分析
    print("\n🎯 Joint Tracking Error Analysis:")
    num_joints = 29
    tracking_errors = []
    
    for i in range(num_joints):
        if f'actual_q_{i}' in df.columns and f'target_q_{i}' in df.columns:
            actual = df[f'actual_q_{i}']
            target = df[f'target_q_{i}']
            error = np.abs(actual - target)
            tracking_errors.append(error.mean())
        else:
            tracking_errors.append(0)
    
    # 显示误差最大的5个关节
    error_sorted = sorted(enumerate(tracking_errors), key=lambda x: x[1], reverse=True)
    print("   Top 5 joints with highest tracking error:")
    for i, (joint_id, error) in enumerate(error_sorted[:5]):
        print(f"      Joint {joint_id}: {error:.4f} rad ({error * 180/np.pi:.2f} deg)")
    
    # 速度命令分析
    print("\n🚀 Velocity Command Analysis:")
    if 'vel_cmd_x' in df.columns:
        print(f"   X velocity: {df['vel_cmd_x'].mean():.3f} ± {df['vel_cmd_x'].std():.3f}")
        print(f"   Y velocity: {df['vel_cmd_y'].mean():.3f} ± {df['vel_cmd_y'].std():.3f}")
        print(f"   Yaw velocity: {df['vel_cmd_yaw'].mean():.3f} ± {df['vel_cmd_yaw'].std():.3f}")
    
    # 创建可视化图表
    create_plots(df, latest_log)

def create_plots(df, log_file):
    """创建分析图表"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f'Robot Control Analysis - {os.path.basename(log_file)}', fontsize=16)
    
    # 1. 关节位置跟踪 (以第一个关节为例)
    if 'actual_q_0' in df.columns and 'target_q_0' in df.columns:
        time_rel = df['timestamp'] - df['timestamp'].iloc[0]
        axes[0, 0].plot(time_rel, df['actual_q_0'], 'b-', label='Actual', alpha=0.7)
        axes[0, 0].plot(time_rel, df['target_q_0'], 'r--', label='Target', alpha=0.7)
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Position (rad)')
        axes[0, 0].set_title('Joint 0 Position Tracking')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 速度命令
    if 'vel_cmd_x' in df.columns:
        time_rel = df['timestamp'] - df['timestamp'].iloc[0]
        axes[0, 1].plot(time_rel, df['vel_cmd_x'], label='X velocity')
        axes[0, 1].plot(time_rel, df['vel_cmd_y'], label='Y velocity')
        axes[0, 1].plot(time_rel, df['vel_cmd_yaw'], label='Yaw velocity')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Velocity')
        axes[0, 1].set_title('Velocity Commands')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
    
    # 3. FSM状态时间线
    if 'fsm_state' in df.columns:
        time_rel = df['timestamp'] - df['timestamp'].iloc[0]
        states = df['fsm_state'].unique()
        state_to_num = {state: i for i, state in enumerate(states)}
        state_nums = [state_to_num[state] for state in df['fsm_state']]
        
        axes[1, 0].plot(time_rel, state_nums, 'o-', markersize=2)
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('FSM State')
        axes[1, 0].set_title('FSM State Timeline')
        axes[1, 0].set_yticks(range(len(states)))
        axes[1, 0].set_yticklabels(states)
        axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 关节跟踪误差直方图
    if 'actual_q_0' in df.columns and 'target_q_0' in df.columns:
        error = df['actual_q_0'] - df['target_q_0']
        axes[1, 1].hist(error, bins=50, alpha=0.7, edgecolor='black')
        axes[1, 1].set_xlabel('Tracking Error (rad)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].set_title('Joint 0 Tracking Error Distribution')
        axes[1, 1].grid(True, alpha=0.3)
        
        # 添加统计信息
        axes[1, 1].axvline(error.mean(), color='red', linestyle='--', 
                          label=f'Mean: {error.mean():.4f}')
        axes[1, 1].axvline(error.std(), color='orange', linestyle='--', 
                          label=f'Std: {error.std():.4f}')
        axes[1, 1].legend()
    
    plt.tight_layout()
    
    # 保存图表
    plot_filename = log_file.replace('.csv', '_analysis.png')
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
    print(f"📈 Analysis plots saved to: {plot_filename}")
    
    # 显示图表（如果在支持的环境中）
    try:
        plt.show()
    except:
        print("   (Plot display not available in this environment)")

def compare_logs():
    """比较多个日志文件的性能"""
    log_files = glob.glob("log/robot_control_*.csv")
    if len(log_files) < 2:
        print("❌ Need at least 2 log files for comparison")
        return
    
    print(f"📊 Comparing {len(log_files)} log files:")
    
    comparison_data = []
    for log_file in log_files:
        df = pd.read_csv(log_file)
        
        # 计算关节0的跟踪误差
        if 'actual_q_0' in df.columns and 'target_q_0' in df.columns:
            error = np.abs(df['actual_q_0'] - df['target_q_0'])
            mean_error = error.mean()
        else:
            mean_error = 0
        
        # 计算控制频率
        duration = df['timestamp'].max() - df['timestamp'].min()
        frequency = len(df) / duration if duration > 0 else 0
        
        comparison_data.append({
            'file': os.path.basename(log_file),
            'records': len(df),
            'duration': duration,
            'frequency': frequency,
            'mean_error': mean_error
        })
    
    # 显示比较结果
    comparison_df = pd.DataFrame(comparison_data)
    print("\n📈 Comparison Results:")
    print(comparison_df.to_string(index=False, float_format='%.3f'))

if __name__ == "__main__":
    print("🔍 Robot Control Log Analysis Tool")
    print("=" * 50)
    
    # 确保log目录存在
    os.makedirs("log", exist_ok=True)
    
    # 分析最新日志
    analyze_latest_log()
    
    print("\n" + "=" * 50)
    
    # 比较多个日志
    compare_logs()
    
    print("\n✅ Analysis complete!")
