# -*- coding: utf-8 -*-
# Author    ： ly
# Datetime  ： 2023/11/2 15:42
# coding:utf-8
import sys

from PySide2.QtCore import QRect, QUrl
from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtGui import QPainter, QImage, QBrush, QColor, QFont, QDesktopServices
from PySide2.QtWidgets import QApplication, QFrame, QHBoxLayout
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (NavigationItemPosition, NavigationWidget, MessageBox,
                            isDarkTheme)
from qfluentwidgets import (SplitFluentWindow,
                            SubtitleLabel, setFont)

from config import AUTHOR
from interface.game_interface import GameInterface
from interface.home_interface import HomeInterface
from interface.loading_interface import Splash
from interface.setting_interface import SettingInterface


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))

        # 为标题栏留出一些空间
        self.hBoxLayout.setContentsMargins(0, 32, 0, 0)


class AvatarWidget(NavigationWidget):
    """ 图标组件 """

    def __init__(self, parent=None):
        super().__init__(isSelectable=False, parent=parent)
        self.avatar = QImage('resource/img/avatar.jpg').scaled(
            24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)

        # draw background
        if self.isEnter:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # draw avatar
        painter.setBrush(QBrush(self.avatar))
        painter.translate(8, 6)
        painter.drawEllipse(0, 0, 24, 24)
        painter.translate(-8, -6)

        if not self.isCompacted:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            font = QFont('Segoe UI')
            font.setPixelSize(14)
            painter.setFont(font)
            painter.drawText(QRect(44, 0, 255, 36), Qt.AlignVCenter, AUTHOR)


class Window(SplitFluentWindow):

    def __init__(self):
        super().__init__()
        self.screen_resolution = self.get_resolution()  # 显示器宽高
        # create sub interface
        self.homeInterface = HomeInterface(self)
        self.musicInterface = Widget('Music Interface', self)
        self.videoInterface = Widget('Video Interface', self)
        self.folderInterface = Widget('Folder Interface', self)
        self.gameInterface = GameInterface(self)
        self.settingInterface = SettingInterface(self)  # 使用自定义设置组件进行替换
        # self.albumInterface = Widget('Album Interface', self)
        # self.albumInterface1 = Widget('Album Interface 1', self)
        # self.albumInterface2 = Widget('Album Interface 2', self)
        self.albumInterface1_1 = Widget('Album Interface 1-1', self)
        self.init_navigation()
        self.init_window()
        self.set_position()

    def init_navigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页')
        self.addSubInterface(self.musicInterface, FIF.MUSIC, '音乐')
        self.addSubInterface(self.videoInterface, FIF.VIDEO, '视频')
        self.addSubInterface(self.gameInterface, FIF.GAME, '比赛')

        self.navigationInterface.addSeparator()

        # self.addSubInterface(self.albumInterface, FIF.ALBUM, '相册', NavigationItemPosition.SCROLL)
        # self.addSubInterface(self.albumInterface1, FIF.ALBUM, '相册 1', parent=self.albumInterface)
        # self.addSubInterface(self.albumInterface1_1, FIF.ALBUM, '相册 1.1', parent=self.albumInterface1)
        # self.addSubInterface(self.albumInterface2, FIF.ALBUM, '相册 2', parent=self.albumInterface)
        self.addSubInterface(self.folderInterface, FIF.FOLDER, '文件夹', NavigationItemPosition.SCROLL)

        # 在底部添加自定义小部件
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=AvatarWidget(),
            onClick=self.show_message_box,
            position=NavigationItemPosition.BOTTOM
        )

        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)
        # 设置左侧栏展开最大宽度
        self.navigationInterface.setExpandWidth(180)

    def init_window(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon('resource/img/logo.png'))
        self.setWindowTitle("New In's App")

    def show_message_box(self):
        w = MessageBox(
            '支持作者😘',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤\n您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('我会出手')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://github.com/lnnocencezz"))

    @staticmethod
    def get_resolution():
        """
        获取显示器分辨率
        """
        screen = QApplication.primaryScreen().geometry()  # 获取屏幕类并调用geometry()方法获取屏幕大小
        w, h = screen.width(), screen.height()
        return w, h

    def set_position(self):
        """
        设置打开窗口在屏幕居中显示
        """
        screen = app.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    MainWindow = Window()
    splash = Splash(app)
    splash.close()
    MainWindow.show()
    app.exec_()
