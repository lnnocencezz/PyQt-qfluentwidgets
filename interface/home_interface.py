# -*- coding: utf-8 -*-
# Author    ： ly
# Datetime  ： 2023/11/3 17:21
import time

import psutil
from PySide2.QtGui import QColor
from PySide2.QtCore import QThread, Signal, QPoint, QTimer
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import TitleLabel, isDarkTheme, BodyLabel, HeaderCardWidget, ProgressRing, InfoBadgeManager, \
    InfoBadge

from config import cfg
from utils.get_system import get_used_system_info, get_disk_space


@InfoBadgeManager.register('Custom')
class CustomInfoBadgeManager(InfoBadgeManager):
    """ Custom info badge manager """

    def position(self):
        pos = self.target.geometry().center()
        x = pos.x() - self.badge.width() // 2
        y = self.target.y() - self.badge.height() // 2
        return QPoint(x, y)


class DeviceStatusCard(HeaderCardWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setTitle('🖥️ 设备系统信息')
        # self.timer_init()

        self.c_disk_label = BodyLabel("", self)
        self.d_disk_label = BodyLabel("", self)
        self.cpu_label = BodyLabel("", self)
        self.memory_label = BodyLabel("", self)

        self.cpuProgress = ProgressRing(self)
        self.cpuProgress.setTextVisible(True)
        self.cpuProgress.setFixedSize(50, 50)
        self.memoryProgress = ProgressRing(self)
        self.memoryProgress.setTextVisible(True)
        self.memoryProgress.setFixedSize(50, 50)

        self.c_disk_Progress = ProgressRing(self)
        self.c_disk_Progress.setTextVisible(True)
        self.c_disk_Progress.setFixedSize(50, 50)
        self.d_disk_Progress = ProgressRing(self)
        self.d_disk_Progress.setTextVisible(True)
        self.d_disk_Progress.setFixedSize(50, 50)
        # 垂直布局
        self.vBoxLayout = QVBoxLayout()
        self.vBoxLayout.setSpacing(30)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        # 水平布局 添加文字
        self.text_hBoxLayout = QHBoxLayout()
        self.text_hBoxLayout.setSpacing(40)
        self.text_hBoxLayout.setContentsMargins(20, -20, 0, 0)
        self.text_hBoxLayout.addWidget(self.c_disk_label)
        self.text_hBoxLayout.addWidget(self.d_disk_label)
        self.text_hBoxLayout.addWidget(self.cpu_label)
        self.text_hBoxLayout.addWidget(self.memory_label)
        # 在最后插入一段空白
        self.text_hBoxLayout.insertSpacing(-1, 20)

        # 水平布局添加进度环
        self.progress_hBoxLayout = QHBoxLayout()
        self.progress_hBoxLayout.addWidget(self.c_disk_Progress)
        self.progress_hBoxLayout.addWidget(self.d_disk_Progress)
        self.progress_hBoxLayout.addWidget(self.cpuProgress)
        self.progress_hBoxLayout.addWidget(self.memoryProgress)

        # 垂直布局中添加 水平文字布局和水平进度环布局
        self.vBoxLayout.addLayout(self.text_hBoxLayout)
        self.vBoxLayout.addLayout(self.progress_hBoxLayout)

        self.viewLayout.addLayout(self.vBoxLayout)

        self.update_system_data()

    def timer_init(self):
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self.update_system_data)
        self.system_timer.start(2000)

    def update_system_data(self):
        cpu_usage, memory_percent = get_used_system_info()
        c_used_percent = get_disk_space('C:')
        d_used_percent = get_disk_space('D:')
        self.c_disk_Progress.setValue(c_used_percent)
        self.d_disk_Progress.setValue(d_used_percent)
        self.cpuProgress.setValue(cpu_usage)
        self.memoryProgress.setValue(memory_percent)
        # 更新标签文本
        self.c_disk_label.setText(f"C盘已用: {self.c_disk_Progress.value()}%")
        self.d_disk_label.setText(f"D盘已用: {self.d_disk_Progress.value()}%")
        self.cpu_label.setText(f"CPU: {self.cpuProgress.value()}%")
        self.memory_label.setText(f"内存: {self.memoryProgress.value()}%")


class HomeInterface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.title_label = None
        self.bgImg_label = None
        self.setObjectName("homeInterface")

        self.init_ui()
        self.add_title_widget()
        self.add_content_widget()
        self.__setQss()
        cfg.themeChanged.connect(self.__setQss)

    def init_ui(self):
        self.setGeometry(0, 0, 900, 700)
        self.setObjectName("HomeInterface")
        self.show()

    def add_title_widget(self):
        self.title_label = TitleLabel("首页", self)
        self.title_label.setObjectName("home_title_label")
        self.title_label.move(35, 50)

    def add_content_widget(self):
        """
        添加卡片组件
        """
        self.content_widget = QWidget(self)
        self.device_status_card = DeviceStatusCard(self)
        self.vBoxLayout = QVBoxLayout()
        self.vBoxLayout.setContentsMargins(0, 0, 0, 10)
        self.vBoxLayout.addWidget(self.device_status_card)
        self.content_widget.setLayout(self.vBoxLayout)
        self.content_widget.move(10, 110)

    def __setQss(self):
        """ set style sheet """
        # 可以单独设置组件样式
        self.title_label.setObjectName('HomeInterfaceTitleLabel')

        theme = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{theme}/home_interface.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())
