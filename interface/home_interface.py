# -*- coding: utf-8 -*-
# Author    ： ly
# Datetime  ： 2023/11/3 17:21
import os
import sys
import time

import psutil
from PySide2.QtGui import QColor, Qt, QFont
from PySide2.QtCore import QThread, Signal, QPoint, QTimer, QSize, QUrl
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import TitleLabel, isDarkTheme, BodyLabel, HeaderCardWidget, ProgressRing, InfoBadgeManager, \
    InfoBadge, SimpleCardWidget, TransparentToolButton, FluentIcon, PillPushButton, setFont, VerticalSeparator, \
    ImageLabel, PrimaryPushButton, HyperlinkLabel, CaptionLabel, ScrollArea, SingleDirectionScrollArea

from config import cfg, RELEASE_URL
from utils.get_system import get_used_system_info, get_disk_space
from config import APP_NAME


@InfoBadgeManager.register('Custom')
class CustomInfoBadgeManager(InfoBadgeManager):
    """ Custom info badge manager """

    def position(self):
        pos = self.target.geometry().center()
        x = pos.x() - self.badge.width() // 2
        y = self.target.y() - self.badge.height() // 2
        return QPoint(x, y)


class StatisticsWidget(QWidget):
    """ Statistics widget """

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = CaptionLabel(title, self)
        self.valueLabel = BodyLabel(value, self)
        self.vBoxLayout = QVBoxLayout(self)

        self.vBoxLayout.setContentsMargins(16, 0, 16, 0)
        self.vBoxLayout.addWidget(self.valueLabel, 0, Qt.AlignTop)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignBottom)

        setFont(self.valueLabel, 18, QFont.DemiBold)
        self.titleLabel.setTextColor(QColor(96, 96, 96), QColor(206, 206, 206))


class AppInfoCard(SimpleCardWidget):
    """ App information card """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.iconLabel = ImageLabel('resource/img/logo.png', self)
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(70)

        self.nameLabel = TitleLabel(APP_NAME, self)
        self.installButton = PrimaryPushButton('安装', self)
        self.companyLabel = HyperlinkLabel(
            QUrl(RELEASE_URL), 'lnnocencezz Inc.', self)
        self.installButton.setFixedWidth(160)

        self.scoreWidget = StatisticsWidget('平均', '5.0', self)
        self.separator = VerticalSeparator(self)
        self.commentWidget = StatisticsWidget('评论数', '3K', self)

        self.descriptionLabel = BodyLabel(
            f"{APP_NAME} APP 是一个基于 PySide2 的 Fluent Design 风格组件库开发的桌面端软件，包含主页、音乐、电影、比赛、文件等模块，可自定义不同界面的组件搭配。",
            self)
        self.descriptionLabel.setWordWrap(True)

        self.tagButton = PillPushButton('组件库', self)
        self.tagButton.setCheckable(False)
        setFont(self.tagButton, 12)
        self.tagButton.setFixedSize(80, 32)

        self.shareButton = TransparentToolButton(FluentIcon.SHARE, self)
        self.shareButton.setFixedSize(32, 32)
        self.shareButton.setIconSize(QSize(14, 14))

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.statisticsLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.initLayout()

    def initLayout(self):
        self.hBoxLayout.setSpacing(30)
        self.hBoxLayout.setContentsMargins(34, 24, 24, 24)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # name label and install button
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addWidget(self.installButton, 0, Qt.AlignRight)

        # company label
        self.vBoxLayout.addSpacing(3)
        self.vBoxLayout.addWidget(self.companyLabel)

        # statistics widgets
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addLayout(self.statisticsLayout)
        self.statisticsLayout.setContentsMargins(0, 0, 0, 0)
        self.statisticsLayout.setSpacing(10)
        self.statisticsLayout.addWidget(self.scoreWidget)
        self.statisticsLayout.addWidget(self.separator)
        self.statisticsLayout.addWidget(self.commentWidget)
        self.statisticsLayout.setAlignment(Qt.AlignLeft)

        # description label
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # button
        self.vBoxLayout.addSpacing(12)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.buttonLayout.addWidget(self.tagButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.shareButton, 0, Qt.AlignRight)


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
        self.cpuProgress.setFixedSize(60, 60)
        self.memoryProgress = ProgressRing(self)
        self.memoryProgress.setTextVisible(True)
        self.memoryProgress.setFixedSize(60, 60)

        self.c_disk_Progress = ProgressRing(self)
        self.c_disk_Progress.setTextVisible(True)
        self.c_disk_Progress.setFixedSize(60, 60)
        self.d_disk_Progress = ProgressRing(self)
        self.d_disk_Progress.setTextVisible(True)
        self.d_disk_Progress.setFixedSize(60, 60)
        # 垂直布局
        self.vBoxLayout = QVBoxLayout()
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        # 水平布局 添加文字
        self.text_hBoxLayout = QHBoxLayout()
        self.text_hBoxLayout.setSpacing(80)
        self.text_hBoxLayout.addWidget(self.c_disk_label)
        self.text_hBoxLayout.addWidget(self.d_disk_label)
        self.text_hBoxLayout.addWidget(self.cpu_label)
        self.text_hBoxLayout.addWidget(self.memory_label)
        # 在最后插入一段空白
        self.text_hBoxLayout.insertSpacing(-1, 25)

        # 水平布局添加进度环
        self.progress_hBoxLayout = QHBoxLayout()
        self.progress_hBoxLayout.setSpacing(80)
        self.progress_hBoxLayout.addWidget(self.c_disk_Progress)
        self.progress_hBoxLayout.addWidget(self.d_disk_Progress)
        self.progress_hBoxLayout.addWidget(self.cpuProgress)
        self.progress_hBoxLayout.addWidget(self.memoryProgress)

        # 垂直布局中添加 水平文字布局和水平进度环布局
        self.vBoxLayout.addLayout(self.text_hBoxLayout)
        self.vBoxLayout.addLayout(self.progress_hBoxLayout)
        # 垂直布局最底层增加一个空白
        self.vBoxLayout.insertSpacing(-1, 20)

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


class HomeInterface(SingleDirectionScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.title_label = None
        self.bgImg_label = None
        self.setObjectName("homeInterface")

        self.init_ui()
        self.add_title_widget()
        self.add_card_interface()
        self.__setQss()
        cfg.themeChanged.connect(self.__setQss)

    def init_ui(self):
        self.setGeometry(0, 0, 900, 700)
        self.setObjectName("HomeInterfaceView")
        self.show()

    def add_title_widget(self):
        self.title_label = TitleLabel("首页", self)
        self.title_label.setObjectName("home_title_label")
        self.title_label.move(35, 50)

    def add_card_interface(self):
        """
        添加卡片组件
        """
        self.content_widget = QWidget(self)
        self.device_status_card = DeviceStatusCard(self)
        self.simple_card = AppInfoCard()
        self.vBoxLayout = QVBoxLayout()
        self.vBoxLayout.setContentsMargins(0, 0, 0, 10)
        self.vBoxLayout.addWidget(self.device_status_card)
        self.vBoxLayout.addWidget(self.simple_card)
        self.content_widget.setLayout(self.vBoxLayout)
        self.content_widget.setFixedWidth(700)
        self.content_widget.move(10, 110)

    def __setQss(self):
        """ set style sheet """
        # 可以单独设置组件样式
        self.title_label.setObjectName('HomeInterfaceTitleLabel')
        theme = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{theme}/home_interface.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())
