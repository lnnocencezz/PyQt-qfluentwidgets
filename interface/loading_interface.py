# -*- coding: utf-8 -*-
# Author    ： ly
# Datetime  ： 2023/11/30 15:07

from PySide2.QtCore import QEventLoop, QTimer
from PySide2.QtGui import QIcon, QMovie
from PySide2.QtWidgets import QLabel
from qfluentwidgets import SplashScreen, TitleLabel, isDarkTheme
from qframelesswindow import FramelessWindow, TitleBarBase

from config import APP_NAME, cfg


class Splash(FramelessWindow):

    def __init__(self, app):
        super().__init__()
        self.resize(900, 700)
        self.set_position(app)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon('resource/img/logo.png'))

        # 创建splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.add_title_bar()
        self.add_loading_gif()
        self.add_loading_text()

        self.show()

        # create other subinterfaces
        self.createSubInterface()

        # close splash screen
        self.splashScreen.finish()

    def add_title_bar(self):
        # 显示icon 和title
        # title_bar = StandardTitleBar(self.splashScreen)
        # title_bar.setIcon(self.windowIcon())
        # title_bar.setTitle(self.windowTitle())
        # self.splashScreen.setTitleBar(title_bar)
        # 不显示icon 和title 以及最大化最小化关闭按钮
        title_bar = TitleBarBase(self.splashScreen)
        title_bar.minBtn.hide()
        title_bar.maxBtn.hide()
        title_bar.closeBtn.hide()
        self.splashScreen.setTitleBar(title_bar)

    def add_loading_gif(self):
        wait_gif = QMovie("resource/img/loading.gif")
        self.gif_label = QLabel(self.splashScreen)
        self.gif_label.setGeometry(180, 10, 900, 700)
        self.gif_label.setMovie(wait_gif)
        wait_gif.start()

    def add_loading_text(self):
        self.gif_text = TitleLabel(self.splashScreen)
        self.gif_text.setGeometry(300, 65, 900, 60)
        self.gif_text.setText("☕稍等一下,马上就好~~")
        self.gif_text.setStyleSheet("color:#f36919; font-size:5em;font-family:'微软雅黑';")

    def createSubInterface(self):
        loop = QEventLoop(self)
        QTimer.singleShot(3500, loop.quit)
        loop.exec_()

    def set_position(self, app):
        """
        设置打开窗口在屏幕居中显示
        """
        screen = app.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
