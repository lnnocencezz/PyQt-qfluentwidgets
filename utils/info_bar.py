# -*- coding: utf-8 -*-
# Author    ： ly
# Datetime  ： 2023/10/21 10:09
# coding:utf-8
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget

from qfluentwidgets import InfoBarIcon, InfoBar, PushButton, FluentIcon, InfoBarPosition


class InfoBarWidget(QWidget):

    def __init__(self, parent):
        super(InfoBarWidget).__init__(parent)
        self.parent = parent
        self.screen_resolution = parent.screen_resolution

    def create_info_info_bar(self, title, content):
        w = InfoBar(
            icon=InfoBarIcon.INFORMATION,
            title=title,
            content=content,
            orient=Qt.Vertical,  # vertical layout
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        w.addWidget(PushButton('Action'))
        w.show()

    def create_success_info_bar(self, title, content, duration, position):
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.AlignCenter,  # 垂直水平对齐
            isClosable=True,
            position=position,
            duration=duration,
            parent=self
        )

    def create_warning_info_bar(self, title, content, duration, position):
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.AlignCenter,
            isClosable=False,  # disable close button
            position=position,
            duration=duration,
            parent=self
        )

    def create_error_info_bar(self, title, content, duration):
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.AlignCenter,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,  # -1 表示不会自动消失 此时需要设置isClosable=True
            parent=self
        )

    def create_custom_info_bar(self, title, content):
        w = InfoBar.new(
            icon=FluentIcon.ACCEPT,
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        w.setCustomBackgroundColor('white', '#202020')
