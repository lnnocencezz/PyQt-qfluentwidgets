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

    return cpu_usage, memory_percent


def get_disk_space(path):
    usage = psutil.disk_usage(path)
    space_used_percent = usage.percent

    return space_used_percent
