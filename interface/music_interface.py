# -*- coding: utf-8 -*-
# Author    ： ly
# Datetime  ： 2023/11/7 9:50
import configparser
import os
import random
import time
from datetime import datetime

import mutagen
from PySide2.QtCore import QUrl, Qt, QTimer
from PySide2.QtGui import QPixmap
from PySide2.QtMultimedia import QMediaPlayer, QMediaContent
from PySide2.QtWidgets import QTableWidgetItem, QVBoxLayout, QLabel, QHeaderView, QStyleFactory, QGridLayout, \
    QListWidget, QFileDialog, QHBoxLayout, QSpacerItem, QSizePolicy, QAbstractItemView
from qfluentwidgets import TableWidget, ScrollArea, Slider, TitleLabel, PrimaryPushButton, ComboBox, \
    TransparentToolButton, RoundMenu, Action, PrimarySplitPushButton, InfoBarPosition
from qfluentwidgets import isDarkTheme
from qfluentwidgets.components.dialog_box.mask_dialog_base import MaskDialogBase
from qfluentwidgets import FluentIcon as FIF
from config import cfg
from utils.info_bar import InfoBarWidget


class MusicInterface(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.songs_list = []
        self.song_formats = ['mp3', 'm4a', 'flac', 'wav', 'ogg']
        self.setting_filename = 'setting.ini'
        self.player = QMediaPlayer()
        self.cur_path = os.path.abspath(os.path.dirname(__file__))
        self.cur_music_index = 0
        self.cur_playing_song = ''
        self.is_switching = False
        self.is_pause = True
        self.logo = QPixmap("resource/img/music.png")
        # 初始化页面
        self.init_ui()
        self.init_data()
        self.add_title_widget()
        self.add_table_widget()
        self.add_feature_widget()
        self.table_layout.addLayout(self.grid)

        # 定时更新
        self.second_timer = QTimer(self)
        self.second_timer.timeout.connect(self.play_by_mode)
        self.second_timer.start(1000)
        # 设置样式
        self.__set_qss()
        cfg.themeChanged.connect(self.__set_qss)

    def __set_qss(self):
        """ set style sheet """
        # 可以单独设置组件样式
        self.title_widget.setObjectName('MusicInterfaceTitleWidget')

        theme = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{theme}/music_interface.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def init_ui(self):
        """
        初始化子页面
        """
        self.setGeometry(0, 0, 900, 700)
        self.setObjectName("MusicInterface")
        self.show()

    def init_data(self):
        # 如果有初始化setting, 导入setting
        self.load_setting()

    def add_title_widget(self):
        self.logo_label = QLabel(self)
        self.logo_label.setPixmap(self.logo)
        self.logo_label.setFixedSize(48, 48)
        self.logo_label.move(20, 60)

        self.title_widget = TitleLabel('Music Player', self)
        self.title_widget.setMinimumWidth(300)
        self.title_widget.setMinimumHeight(100)
        self.title_widget.move(90, 30)

    def add_table_widget(self):
        """
        创建表格组件
        """
        # 创建水平布局
        self.table_layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)
        self.tableView.doubleClicked.connect(self.double_clicked)
        # 刷新表格数据
        self.refresh_table()
        # 添加按钮
        buttons_layout = QHBoxLayout()
        # 打开文件夹按钮
        self.open_button = PrimaryPushButton('打开文件夹', self, FIF.MUSIC_FOLDER)
        self.open_button.setStyle(QStyleFactory.create('Fusion'))
        self.open_button.clicked.connect(self.open_dir)
        # 播放模式
        self.menu = RoundMenu()
        self.menu.addAction(Action(FIF.SCROLL, '顺序播放'))
        self.menu.addAction(Action(FIF.SYNC, '单曲循环'))
        self.menu.addAction(Action(FIF.CANCEL, '随机播放'))
        self.menu.triggered.connect(self.on_menu_changed)
        # 下拉列表 暂时不用修改为下拉菜单
        # self.cmb = ComboBox()
        # self.cmb.setStyle(QStyleFactory.create('Fusion'))
        # items = ['🔁 列表循环', '🔂 单曲循环', '🔀 随机播放']
        # self.cmb.addItems(items)
        self.mode_change_btn = PrimarySplitPushButton('顺序播放', self, FIF.ALIGNMENT)
        self.mode_change_btn.setFlyout(self.menu)
        buttons_layout.addWidget(self.open_button)
        buttons_layout.addWidget(self.mode_change_btn)
        # 增加空白区域来缩短按钮宽度
        empty_space = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        buttons_layout.addItem(empty_space)
        self.table_layout.addLayout(buttons_layout)

        self.setStyleSheet("Demo{background: rgb(255, 255, 255)} ")
        self.table_layout.setContentsMargins(20, 130, 20, 10)
        self.table_layout.addWidget(self.tableView)

    def add_feature_widget(self):
        """
        添加功能组件
        """
        self.contains_feature = QVBoxLayout()
        # 播放时间
        self.start_point = QLabel('00:00')
        self.start_point.setStyle(QStyleFactory.create('Fusion'))
        self.end_point = QLabel('00:00')
        self.end_point.setStyle(QStyleFactory.create('Fusion'))
        # 上一首按钮
        self.preview_button = TransparentToolButton(FIF.PAGE_LEFT, self)
        self.preview_button.clicked.connect(self.preview_music)
        self.preview_button.setStyle(QStyleFactory.create('Fusion'))
        # 播放按钮
        self.play_button = TransparentToolButton(FIF.PLAY, self)
        self.play_button.clicked.connect(self.play_music)
        self.play_button.setStyle(QStyleFactory.create('Fusion'))
        # 暂停按钮
        self.pause_button = TransparentToolButton(FIF.PAUSE, self)
        self.pause_button.clicked.connect(self.play_music)
        self.pause_button.setStyle(QStyleFactory.create('Fusion'))
        self.pause_button.hide()
        # 下一首按钮
        self.next_button = TransparentToolButton(FIF.PAGE_RIGHT, self)
        self.next_button.clicked.connect(self.next_music)
        self.next_button.setStyle(QStyleFactory.create('Fusion'))
        # 进度条
        self.slider = Slider(Qt.Horizontal, self)
        self.slider.sliderMoved[int].connect(lambda: self.player.setPosition(self.slider.value()))
        self.slider.setStyle(QStyleFactory.create('Fusion'))
        #  音量开
        self.volume_button = TransparentToolButton(FIF.VOLUME, self)
        self.volume_button.setStyle(QStyleFactory.create('Fusion'))
        self.volume_button.clicked.connect(self.toggle_mute)
        #  音量关
        self.volume_mute_button = TransparentToolButton(FIF.MUTE, self)
        self.volume_mute_button.setStyle(QStyleFactory.create('Fusion'))
        self.volume_mute_button.clicked.connect(self.toggle_mute)
        self.volume_mute_button.hide()
        # 音量条
        self.volume_slider = Slider(Qt.Horizontal, self)
        self.volume_slider.valueChanged.connect(self.volume_changed)
        self.volume_slider.setStyle(QStyleFactory.create('Fusion'))
        # 初始化时设置
        self.volume_slider.setValue(50)
        self.volume_slider.setMinimumWidth(10)
        # 界面布局
        self.grid = QGridLayout()
        self.grid.addWidget(self.preview_button, 0, 0, 1, 1)
        self.grid.addWidget(self.play_button, 0, 1, 1, 1)
        self.grid.addWidget(self.pause_button, 0, 1, 1, 1)
        self.grid.addWidget(self.next_button, 0, 2, 1, 1)
        self.grid.addWidget(self.start_point, 0, 3, 1, 1)
        self.grid.addWidget(self.slider, 0, 10, 1, 20)
        self.grid.addWidget(self.end_point, 0, 31, 1, 1)
        self.grid.addWidget(self.volume_button, 0, 32, 1, 1)
        self.grid.addWidget(self.volume_mute_button, 0, 32, 1, 1)
        self.grid.addWidget(self.volume_slider, 0, 50, 1, 5)
        self.grid.addLayout(self.contains_feature, 0, 51, 1, 1)

    def refresh_table(self):
        """
        刷新表格数据
        """
        # 清空旧的数据
        self.tableView.setRowCount(0)
        # enable border
        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)

        # 重新添加行列
        self.tableView.setWordWrap(False)
        # 设置固定行数
        # self.tableView.setRowCount(50)
        # 设置列数
        self.tableView.setColumnCount(4)

        # 设置行高
        row_height = 36
        for i, row in enumerate(self.songs_list):
            self.tableView.insertRow(i)
            self.tableView.setRowHeight(i, row_height)

            for j, data in enumerate(row):
                self.tableView.setItem(i, j, QTableWidgetItem(row[data]))
                if self.tableView.item(i, j):
                    self.tableView.item(i, j).setData(Qt.UserRole, i)

        # 设置表头
        self.tableView.verticalHeader().hide()
        self.tableView.setHorizontalHeaderLabels(['歌曲名', '歌手', '专辑', '时长'])
        self.tableView.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background-color:rgb(96, 155, 206);color: white;};"
        )
        # 允许排序
        self.tableView.setSortingEnabled(True)
        # 自适应
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)
        # 禁止编辑
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 设置居中
        for c in range(self.tableView.columnCount()):
            for r in range(self.tableView.rowCount()):
                if self.tableView.item(r, c) is not None:
                    self.tableView.item(r, c).setTextAlignment(Qt.AlignCenter)

    def open_dir(self):
        """
        打开文件夹
        """
        self.cur_path = QFileDialog.getExistingDirectory(self, "选取文件夹", self.cur_path)
        if self.cur_path:
            self.show_music_list()
            self.cur_playing_song = ''
            self.set_cur_playing(0)
            self.start_point.setText('00:00')
            self.end_point.setText('00:00')
            self.slider.setSliderPosition(0)
            self.is_pause = True
            self.play_button.show()

    def play_by_mode(self):
        """
        播放模式
        """
        if (not self.is_pause) and (not self.is_switching):
            self.slider.setMinimum(0)
            self.slider.setMaximum(self.player.duration())
            self.slider.setValue(self.slider.value() + 1000)
        self.start_point.setText(time.strftime('%M:%S', time.localtime(self.player.position() / 1000)))
        self.end_point.setText(time.strftime('%M:%S', time.localtime(self.player.duration() / 1000)))
        # 顺序播放
        if (self.mode_change_btn.text() == "顺序播放") and (not self.is_pause) and (not self.is_switching):
            if len(self.songs_list) == 0:
                return
            if self.player.position() == self.player.duration():
                self.next_music()
        # 单曲循环
        elif (self.mode_change_btn.text() == "单曲循环") and (not self.is_pause) and (not self.is_switching):
            if len(self.songs_list) == 0:
                return
            if self.player.position() == self.player.duration():
                self.is_switching = True
                self.set_cur_playing(self.cur_music_index)
                self.slider.setValue(0)
                self.play_music()
                self.is_switching = False
        # 随机播放
        elif (self.mode_change_btn.text() == "随机播放") and (not self.is_pause) and (not self.is_switching):
            if len(self.songs_list) == 0:
                return
            if self.player.position() == self.player.duration():
                self.is_switching = True
                random_index = random.randint(0, len(self.songs_list) - 1)
                self.set_cur_playing(random_index)
                self.slider.setValue(0)
                self.play_music()
                self.is_switching = False

    def double_clicked(self, row):
        """
        双击列表播放音乐
        """
        row_index = row.row()
        col_index = 0

        item = self.tableView.item(row_index, col_index)
        self.cur_music_index = item.data(Qt.UserRole)
        self.slider.setValue(0)
        self.is_switching = True
        self.set_cur_playing(self.cur_music_index)
        self.play_music()
        self.is_switching = False

    def load_setting(self):
        """
         导入setting
        """
        if os.path.isfile(self.setting_filename):
            config = configparser.ConfigParser()
            config.read(self.setting_filename)
            self.cur_path = config.get('MusicPlayer', 'PATH')
            self.show_music_list()

    def show_music_list(self):
        """
        显示文件夹中所有音乐
        """
        self.update_setting()
        for song in os.listdir(self.cur_path):
            if song.split('.')[-1] in self.song_formats:
                meta = self.get_audio_meta(os.path.join(self.cur_path, song).replace('\\', '/'))
                self.songs_list.append(meta)

        if self.songs_list:
            self.cur_playing_song = self.songs_list[self.cur_music_index]['title']

    def update_setting(self):
        """
        更新setting
        """
        config = configparser.ConfigParser()
        config.read(self.setting_filename)
        if not os.path.isfile(self.setting_filename):
            config.add_section('MusicPlayer')
        config.set('MusicPlayer', 'PATH', self.cur_path)
        config.write(open(self.setting_filename, 'w'))

    def get_audio_meta(self, filepath):
        """
        获取音频文件元信息
        """
        audio = mutagen.File(filepath)

        title = audio.tags.get("title", ["Unknown Title"])[0]
        artist = audio.tags.get("artist", ["Unknown Artist"])[0]
        album = audio.tags.get("album", ["Unknown Album"])[0]
        duration = "%02d:%02d" % (audio.info.length // 60, audio.info.length % 60)
        meta_info = {
            "title": title,
            "artist": artist,
            "album": album,
            "duration": duration,
            "path": filepath
        }

        return meta_info

    def set_cur_playing(self, index):
        """
        设置当前播放
        """
        self.cur_playing_song = self.songs_list[index]['title']
        self.cur_music_index = index
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.songs_list[index]["path"])))

    def play_music(self):
        """
        播放音乐
        """
        if len(self.songs_list) == 0:
            InfoBarWidget.create_warning_info_bar(self, "提示信息", "当前路径内无可播放的音乐文件", 1500)
            return
        if not self.player.isAudioAvailable():
            self.set_cur_playing(self.cur_music_index)
        if self.is_pause or self.is_switching:
            # 暂停
            self.player.play()
            self.is_pause = False
            self.play_button.hide()
            self.pause_button.show()
        elif (not self.is_pause) and (not self.is_switching):
            # 播放
            self.player.pause()
            self.is_pause = True
            self.play_button.show()
            self.pause_button.hide()
        self.tableView.selectRow(self.cur_music_index)

    def preview_music(self):
        """上一首"""
        if self.mode_change_btn.text() == "随机播放":
            # 如果是随机模式则需要
            index = random.randint(0, len(self.songs_list) - 1)
        else:
            index = self.cur_music_index - 1
        if index < 0:
            index = len(self.songs_list) - 1
        self.play_music_by_index(index)

    def next_music(self):
        """下一首"""
        if self.mode_change_btn.text() == "随机播放":
            # 如果是随机模式则需要
            index = random.randint(0, len(self.songs_list) - 1)
        else:
            index = self.cur_music_index + 1
        if index >= len(self.songs_list):
            index = 0

        self.play_music_by_index(index)

    def play_music_by_index(self, index):
        """
        修改当前播放的歌曲索引
        """
        self.slider.setValue(0)
        self.is_switching = True
        self.set_cur_playing(index)
        self.play_music()
        self.is_switching = False

    def toggle_mute(self):
        """
        音量条调整
        """
        if self.player.volume() == 0:
            self.player.setVolume(50)
            self.volume_slider.setValue(50)
            self.volume_button.show()
            self.volume_mute_button.hide()
        else:
            self.player.setVolume(0)
            self.volume_slider.setValue(0)
            self.volume_button.hide()
            self.volume_mute_button.show()

    def volume_changed(self, value):
        """
        音量调整
        """
        self.player.setVolume(value)

    def on_menu_changed(self, action):
        """
        菜单栏播放模式切换
        """
        selected_text = action.text()
        self.mode_change_btn.setText(selected_text)
        InfoBarWidget.create_success_info_bar(self, "模式切换成功", f"当前模式已切换为：【{selected_text}】", 2000, InfoBarPosition.TOP_RIGHT)
