# -*- coding: utf-8 -*-
# Author    ： ly
# Datetime  ： 2023/11/7 9:50
import time
from datetime import datetime

from PySide2.QtCore import QUrl, Qt, QThread, Signal, QTimer
from PySide2.QtGui import QPixmap, QDesktopServices
from PySide2.QtWidgets import QTableWidgetItem, QHBoxLayout, QVBoxLayout, QLabel, QLCDNumber
from qfluentwidgets import FluentIcon as FIF, PrimaryPushButton, isDarkTheme, LineEdit, MessageBox, StateToolTip, \
    ToolTipFilter, ToolTipPosition
from qfluentwidgets import TableWidget, ScrollArea, SubtitleLabel, CalendarPicker
from qfluentwidgets import TitleLabel, MessageBoxBase

from config import cfg
from utils.get_data import GameData
from utils.info_bar import InfoBarWidget


# 工作线程类
class Worker(QThread):
    """
    另起线程获取网页数据
    """
    dataReady = Signal(object)  # 定义信号

    def run(self):
        """
        默认获取当日数据
        """
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        url = f'https://nba.hupu.com/games/{today_str}'
        data = GameData(url).parse_links()
        self.dataReady.emit(data)


class CustomDatePickBox(MessageBoxBase):
    """ 日期选择弹出框 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('日期选择', self)

        self.picker = CalendarPicker(self)
        self.picker.setText('选择日期，获取当日比赛数据')
        self.picker.setDateFormat(Qt.TextDate)
        self.picker.setDateFormat('yyyy-M-d')

        # add widget to view layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.picker)

        # change the text of button
        self.yesButton.setText('确认')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(350)
        self.yesButton.setDisabled(True)
        self.picker.dateChanged.connect(self._validateUrl)

    def _validateUrl(self, date):
        date_str = date.toString(Qt.ISODate)
        self.yesButton.setEnabled(QUrl(date_str).isValid())


class CustomTotalBox(MessageBoxBase):
    """ 统计数据弹出框 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('输入球员', self)
        self.urlLineEdit = LineEdit(self)

        self.urlLineEdit.setPlaceholderText('请输入球员姓名,以空格分隔:')
        self.urlLineEdit.setClearButtonEnabled(True)

        # add widget to view layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.urlLineEdit)

        # change the text of button
        self.yesButton.setText('确认')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(350)
        self.yesButton.setDisabled(True)
        self.urlLineEdit.textChanged.connect(self._validateUrl)

        # self.hideYesButton()

    def _validateUrl(self, text):
        self.yesButton.setEnabled(QUrl(text).isValid())


class GameInterface(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.title_label = None
        self.url = None
        self.players_data = []
        self.team_scores = []
        self.logo = QPixmap("resource/img/nba.png")
        self.selected_date = datetime.now().strftime("%Y-%m-%d")
        self.init_ui()
        self.init_data()
        self.create_timer()

        self.add_title_widget()
        self.add_table_widget()
        # 设置样式
        self.__setQss()
        cfg.themeChanged.connect(self.__setQss)

    def init_ui(self):
        self.setGeometry(0, 0, 900, 700)
        self.setObjectName("GameInterface")
        self.show()
        InfoBarWidget.create_warning_info_bar(self, "提示信息", "数据正在全力🏃‍➡️加载中，请耐心等待☕", 1500)

    def create_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_lcd)
        self.timer.start(1000)  # 1秒触发一次

    def update_lcd(self):
        time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        self.lcd.display(time_str)

    def __setQss(self):
        """ set style sheet """
        # 可以单独设置组件样式
        self.title_widget.setObjectName('GameInterfaceTitleWidget')

        theme = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{theme}/game_interface.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def init_data(self):
        # 创建线程 异步获取数据
        self.thread = Worker()
        self.thread.dataReady.connect(self.on_data_ready)  # 连接信号
        # 触发获取数据
        self.thread.start()

    # 槽函数
    def on_data_ready(self, data):
        """
        数据另起一个线程进行加载
        """
        if not data:
            InfoBarWidget.create_error_info_bar(self, "失败", "今日📅暂无比赛或无球员数据更新", 5000)
            return
        self.players_data = data['players']
        self.team_scores = data['scores']
        self.refresh_table()  # 在线程完成后添加表格

    def add_title_widget(self):
        self.logo_label = QLabel(self)
        self.logo_label.setPixmap(self.logo)
        self.logo_label.setFixedSize(48, 48)
        self.logo_label.move(20, 60)

        self.title_widget = TitleLabel('NBA Player Stats', self)
        self.title_widget.setMinimumWidth(300)
        self.title_widget.setMinimumHeight(100)
        self.title_widget.move(80, 30)

        self.lcd = QLCDNumber(self)
        self.lcd.setObjectName('GameInterfaceLcdWidget')
        self.lcd.setDigitCount(19)
        self.lcd.setMode(QLCDNumber.Dec)

        self.lcd.setStyleSheet(
            """
            background-color: rgb(56, 56, 56);
            border: 4px solid #f5cd92;
            color: white;
            border-radius: 20px;
            font-size: 55px;
            font-weight: 700;
            """
        )
        self.lcd.resize(250, 40)
        self.lcd.move(550, 65)

    def add_table_widget(self):
        """
        创建表格组件
        """
        # 创建水平布局
        self.table_layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)

        self.refresh_table()

        # 添加按钮
        buttons_layout = QHBoxLayout()
        self.popup_btn = PrimaryPushButton('选择日期', self, FIF.CALENDAR)
        self.check_score_btn = PrimaryPushButton('查看比分', self, FIF.BASKETBALL)
        self.refresh_btn = PrimaryPushButton('刷新数据', self, FIF.UPDATE)
        self.total_btn = PrimaryPushButton('统计数据', self, FIF.LABEL)
        # 设置按钮提示
        self.popup_btn.setToolTip('选择日期后会显示当日比赛数据')
        # 设置延时隐藏 -1 代表不隐藏
        self.popup_btn.setToolTipDuration(1000)
        # 设置延时显示 0代表零延时
        self.popup_btn.installEventFilter(ToolTipFilter(self.popup_btn, 0, ToolTipPosition.TOP))

        buttons_layout.addWidget(self.popup_btn)
        buttons_layout.addWidget(self.check_score_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addWidget(self.total_btn)

        self.table_layout.addLayout(buttons_layout)
        self.setStyleSheet("Demo{background: rgb(255, 255, 255)} ")
        self.table_layout.setContentsMargins(20, 130, 20, 10)
        self.table_layout.addWidget(self.tableView)

        self.refresh_btn.clicked.connect(self.on_clicked)
        self.popup_btn.clicked.connect(self.show_dialog)
        self.total_btn.clicked.connect(self.on_total_btn_clicked)
        self.check_score_btn.clicked.connect(self.on_check_score_btn_clicked)

    def show_dialog(self):
        """
        弹出框输入日期
        """
        w = CustomDatePickBox(self)
        if w.exec():
            self.selected_date = w.picker.text()
            self.url = f'https://nba.hupu.com/games/{self.selected_date}'
            result = GameData(self.url).parse_links()
            self.players_data = result['players']
            self.team_scores = result['scores']
            self.refresh_table()
            InfoBarWidget.create_success_info_bar(self, "刷新数据", "数据更新成功", 1500)

    # 随机生成数据
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
        # 设置行数
        self.tableView.setRowCount(120)
        # 设置列数
        self.tableView.setColumnCount(11)

        # 设置行高
        row_height = 36
        for i, row in enumerate(self.players_data):
            self.tableView.insertRow(i)
            self.tableView.setRowHeight(i, row_height)

            for j, data in enumerate(row):
                self.tableView.setItem(i, j, QTableWidgetItem(data))

        # 设置表头
        self.tableView.verticalHeader().hide()
        self.tableView.setHorizontalHeaderLabels(
            ['姓名', '球队', '得分', '篮板', '助攻', '抢断', '盖帽', '失误', '犯规', '正负值', '战力值'])
        self.tableView.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background-color:rgb(96, 155, 206);color: white;};"
        )
        self.tableView.setColumnWidth(0, 150)  # 再手动设置第一列为150
        self.tableView.setColumnWidth(1, 90)
        self.tableView.setColumnWidth(2, 61)
        self.tableView.setColumnWidth(3, 61)
        self.tableView.setColumnWidth(4, 61)
        self.tableView.setColumnWidth(5, 61)
        self.tableView.setColumnWidth(6, 61)
        self.tableView.setColumnWidth(7, 61)
        self.tableView.setColumnWidth(8, 61)
        self.tableView.setColumnWidth(9, 65)
        self.tableView.setColumnWidth(10, 65)
        # 设置居中
        for c in range(self.tableView.columnCount()):
            for r in range(self.tableView.rowCount()):
                if self.tableView.item(r, c) is not None:
                    self.tableView.item(r, c).setTextAlignment(Qt.AlignCenter)

        # 允许排序
        self.tableView.setSortingEnabled(True)

    def on_clicked(self):
        """
        自动/手动刷新数据
        """
        if not self.url:
            # 没选择新日期,重新获取当日数据
            self.init_data()
        else:
            self.refresh_table()
        InfoBarWidget.create_success_info_bar(self, "刷新数据", "数据更新成功", 1500)

    def on_total_btn_clicked(self):
        w = CustomTotalBox(self)
        if w.exec():
            name_list = w.urlLineEdit.text().split(' ')
            player_data = self.players_data
            print(player_data)
            selected = [p for p in player_data if p[0] in name_list]
            # print(selected)
            total = sum(float(p[-1]) for p in selected)
            InfoBarWidget.create_success_info_bar(self, '统计结果',
                                                  f'选中球员为【{", ".join(name_list)}】\n战力值合计:【{total}】', -1)

    def on_check_score_btn_clicked(self):
        score_text = ""
        for _ in self.team_scores:
            # 判断胜利球队,并将比分用HTML标记
            home_team = _["home_team"]
            home_score = _["home_score"]
            away_score = _["away_score"]
            away_team = _["away_team"]
            print(home_team, home_score, away_score, away_team)
            if int(home_score) > int(away_score):
                score_text += '<h3>{} (主) <font color="red">{}</font> - {} {} </h3>'.format(home_team, home_score,away_score, away_team)
            else:
                score_text += '<h3>{} (主) {} - <font color="red">{}</font> {} </h3>'.format(home_team, home_score,away_score, away_team)

        w = MessageBox(
            f'比赛日期: 📅 {self.selected_date}',
            score_text,
            self
        )
        w.yesButton.setText('知道了')
        w.cancelButton.setText('下次一定')

        if w.exec():
            pass

    def onButtonClicked(self):
        if self.stateTooltip:
            self.stateTooltip.setContent('模型训练完成啦 😆')
            self.stateTooltip.setState(True)
            self.stateTooltip = None
        else:
            self.stateTooltip = StateToolTip('正在训练模型', '客官请耐心等待哦~~', self)
            self.stateTooltip.move(510, 30)
            self.stateTooltip.show()