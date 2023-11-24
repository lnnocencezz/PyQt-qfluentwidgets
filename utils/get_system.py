# -*- coding: utf-8 -*-
# Author    ： ly
# Datetime  ： 2023/11/14 8:53
import psutil


def get_used_system_info():
    # 获取CPU使用率
    cpu_usage = psutil.cpu_percent(interval=1)
    # 获取内存使用情况
    memory_info = psutil.virtual_memory()
    memory_percent = memory_info.percent
    # 指定磁盘path为C:\
    target_disk = 'C:\\'
    disk_usage = psutil.disk_usage(target_disk)
    # 打印磁盘使用情况
    # print(f"CPU当前使用率：{cpu_usage}%")
    # print(f"Memory当前使用率：{memory_percent}%")
    # print(f"磁盘路径: {target_disk}")
    # print(f"总容量: {disk_usage.total / (1024 ** 3):.2f} GB")  # 将字节转换为GB
    # print(f"已用空间: {disk_usage.used / (1024 ** 3):.2f} GB")
    # print(f"可用空间: {disk_usage.free / (1024 ** 3):.2f} GB")
    # print(f"使用率: {disk_usage.percent}%")

    return cpu_usage, memory_percent


def get_disk_space(path):
    usage = psutil.disk_usage(path)
    space_used_percent = usage.percent

    return space_used_percent
