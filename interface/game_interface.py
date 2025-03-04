# -*- coding: utf-8 -*-
# Author    ： ly
# Datetime  ： 2023/11/7 9:50
import time
import difflib
import re
from datetime import datetime

from PySide2.QtCore import QUrl, Qt, QThread, Signal, QTimer
from PySide2.QtGui import QPixmap, QDesktopServices
from PySide2.QtWidgets import QTableWidgetItem, QHBoxLayout, QVBoxLayout, QLabel, QLCDNumber, QHeaderView, QFileDialog
from qfluentwidgets import FluentIcon as FIF, PrimaryPushButton, isDarkTheme, LineEdit, MessageBox, StateToolTip, \
    ToolTipFilter, ToolTipPosition, InfoBarPosition
from qfluentwidgets import TableWidget, ScrollArea, SubtitleLabel, CalendarPicker
from qfluentwidgets import TitleLabel, MessageBoxBase

from config import cfg
from utils.get_data import GameData
from utils.info_bar import InfoBarWidget
from utils.ocr import extract_chinese_names


# 工作线程类（用于获取网页数据）
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


# 新线程类（用于 OCR 识别和统计）
class OCRWorker(QThread):
    """
    另起线程执行 OCR 识别和统计任务
    """
    resultReady = Signal(tuple)  # 信号：返回统计结果 (match_player, total_power)
    errorOccurred = Signal(str)  # 信号：返回错误信息

    def __init__(self, file_path, players_data):
        super().__init__()
        self.file_path = file_path
        self.players_data = players_data

    def run(self):
        try:
            # 调用 OCR 识别函数
            player_names = extract_chinese_names(self.file_path)
            if not player_names or "错误" in player_names[0]:
                self.errorOccurred.emit("未能识别图片中的球员名字")
                return

            # 清洗并格式化球员名字
            player_names = [name for name in player_names if "名字未识别" not in name]
            if not player_names:
                self.errorOccurred.emit("未能识别有效的球员名字")
                return

            # 使用识别出的球员名字进行统计
            result = self.search(self.players_data, player_names)
            self.resultReady.emit(result)

        except Exception as e:
            self.errorOccurred.emit(f"处理失败: {str(e)}")

    @staticmethod
    def search(player_lst, name_lst):
        cp = 0
        match_player = []

        # 手动映射字典：将 OCR 识别出的名字映射到hupu中的球员名字
        name_mapping = {
            "贾伦·杜伦": "杰伦-杜伦",
            "小贾伦·杰克逊": "格雷格-杰克逊二世",
            "沃克·科斯勒": "沃克-凯斯勒",
        }

        def normalize_name(name):
            """规范化名字：统一分隔符、去除多余空格、转换为小写（英文部分）"""
            name = re.sub(r'\s+', '', name)
            name = name.replace('·', '-').replace('.', '-')
            return name.lower()

        for name in name_lst:
            mapped_name = name_mapping.get(name.replace('-', ''), name)
            mapped_name = name_mapping.get(mapped_name, mapped_name)
            normalized_name = normalize_name(mapped_name)

            for player in player_lst:
                player_name = player[0]
                normalized_player_name = normalize_name(player_name)

                if normalized_name in normalized_player_name:
                    print(f"匹配成功: {player_name} (识别: {name}, 映射后: {mapped_name})")
                    match_player.append(player_name)
                    cp += float(player[-1])
                    break
                else:
                    similarity = difflib.SequenceMatcher(None, normalized_name, normalized_player_name).ratio()
                    if similarity > 0.9:
                        print(
                            f"模糊匹配成功: {player_name} (识别: {name}, 映射后: {mapped_name}, 相似度: {similarity:.2f})")
                        match_player.append(player_name)
                        cp += float(player[-1])
                        break

        print("合计：", round(cp, 2))
        return match_player, round(cp, 2)


class CustomDatePickBox(MessageBoxBase):
    """ 日期选择弹出框 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('日期选择', self)

        self.picker = CalendarPicker(self)
        self.picker.setText('选择日期，获取当日比赛数据')
        self.picker.setDateFormat(Qt.TextDate)
        self.picker.setDateFormat('yyyy-M-d')

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.picker)

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

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.urlLineEdit)

        self.yesButton.setText('确认')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(350)
        self.yesButton.setDisabled(True)
        self.urlLineEdit.textChanged.connect(self._validateUrl)

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
        self.stateTooltip = None
        self.ocr_thread = None  # 用于存储 OCR 线程
        self.init_ui()
        self.init_data()
        self.create_timer()

        self.add_title_widget()
        self.add_table_widget()
        self.__setQss()
        cfg.themeChanged.connect(self.__setQss)

    def init_ui(self):
        self.setGeometry(0, 0, 900, 700)
        self.setObjectName("GameInterface")
        self.show()
        InfoBarWidget.create_warning_info_bar(self, "提示信息", "数据正在全力加载中~", 1500,
                                              InfoBarPosition.BOTTOM_RIGHT)

    def create_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_lcd)
        self.timer.start(1000)

    def update_lcd(self):
        time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        self.lcd.display(time_str)

    def __setQss(self):
        self.title_widget.setObjectName('GameInterfaceTitleWidget')

        theme = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{theme}/game_interface.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def init_data(self):
        self.thread = Worker()
        self.thread.dataReady.connect(self.on_data_ready)
        self.thread.start()

    def on_data_ready(self, data):
        if not data:
            InfoBarWidget.create_error_info_bar(self, "失败", "今日📅暂无比赛或无球员数据更新", 5000)
            return
        self.players_data = data['players']
        self.team_scores = data['scores']
        self.refresh_table()

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
        self.lcd.move(450, 65)

    def add_table_widget(self):
        self.table_layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)

        self.refresh_table()

        buttons_layout = QHBoxLayout()
        self.popup_btn = PrimaryPushButton('选择日期', self, FIF.CALENDAR)
        self.check_score_btn = PrimaryPushButton('查看比分', self, FIF.BASKETBALL)
        self.refresh_btn = PrimaryPushButton('刷新数据', self, FIF.UPDATE)
        self.upload_btn = PrimaryPushButton('上传图片', self, FIF.FOLDER)

        self.popup_btn.setToolTip('选择日期后会显示当日比赛数据')
        self.check_score_btn.setToolTip('点击后即可查看当日比赛数据')
        self.refresh_btn.setToolTip('点击后立即刷新球员数据')
        self.upload_btn.setToolTip('上传图片后通过OCR识别球员名字并统计战力值')

        self.popup_btn.setToolTipDuration(3000)
        self.check_score_btn.setToolTipDuration(3000)
        self.refresh_btn.setToolTipDuration(3000)
        self.upload_btn.setToolTipDuration(3000)

        self.popup_btn.installEventFilter(ToolTipFilter(self.popup_btn, 0, ToolTipPosition.TOP))
        self.check_score_btn.installEventFilter(ToolTipFilter(self.check_score_btn, 0, ToolTipPosition.TOP))
        self.refresh_btn.installEventFilter(ToolTipFilter(self.refresh_btn, 0, ToolTipPosition.TOP))
        self.upload_btn.installEventFilter(ToolTipFilter(self.upload_btn, 0, ToolTipPosition.TOP))

        buttons_layout.addWidget(self.popup_btn)
        buttons_layout.addWidget(self.check_score_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addWidget(self.upload_btn)

        self.table_layout.addLayout(buttons_layout)
        self.setStyleSheet("Demo{background: rgb(255, 255, 255)} ")
        self.table_layout.setContentsMargins(20, 130, 20, 10)
        self.table_layout.addWidget(self.tableView)

        self.refresh_btn.clicked.connect(self.on_clicked)
        self.popup_btn.clicked.connect(self.show_dialog)
        self.check_score_btn.clicked.connect(self.on_check_score_btn_clicked)
        self.upload_btn.clicked.connect(self.on_upload_btn_clicked)

    def on_upload_btn_clicked(self):
        """
        处理上传图片按钮点击事件
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Image Files (*.png *.jpg *.jpeg)")
        if not file_path:
            InfoBarWidget.create_warning_info_bar(self, "提示", "未选择图片", 1500, InfoBarPosition.TOP)
            return

        # 显示加载提示
        self.onButtonClicked()

        # 创建 OCR 线程并启动
        self.ocr_thread = OCRWorker(file_path, self.players_data)
        self.ocr_thread.resultReady.connect(self.on_ocr_result_ready)
        self.ocr_thread.errorOccurred.connect(self.on_ocr_error)
        self.ocr_thread.start()

    def on_ocr_result_ready(self, result):
        """
        处理 OCR 线程完成后的结果
        """
        self.stateTooltip.setContent('统计完成啦 😆')
        self.stateTooltip.setState(True)
        self.stateTooltip = None
        InfoBarWidget.create_success_info_bar(self, '统计结果',
                                              f'您选择的球员为：\n【{", ".join(result[0])}】\n战力值合计:【{result[1]}】',
                                              5000,
                                              InfoBarPosition.TOP_RIGHT)

    def on_ocr_error(self, error_msg):
        """
        处理 OCR 线程中的错误
        """
        self.stateTooltip.setContent('识别失败 😞')
        self.stateTooltip.setState(True)
        self.stateTooltip = None
        InfoBarWidget.create_error_info_bar(self, "失败", error_msg, 5000)

    def show_dialog(self):
        w = CustomDatePickBox(self)
        if w.exec():
            self.selected_date = w.picker.text()
            self.url = f'https://nba.hupu.com/games/{self.selected_date}'
            result = GameData(self.url).parse_links()
            self.players_data = result['players']
            self.team_scores = result['scores']
            self.refresh_table()
            InfoBarWidget.create_success_info_bar(self, "刷新数据", "数据更新成功", 1500, InfoBarPosition.TOP_RIGHT)

    def refresh_table(self):
        # 清空表格内容但保留结构
        self.tableView.setRowCount(0)
        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)
        self.tableView.setWordWrap(False)
        self.tableView.setColumnCount(11)

        # 填充数据
        row_height = 36
        for i, row in enumerate(self.players_data):
            self.tableView.insertRow(i)
            self.tableView.setRowHeight(i, row_height)
            for j, data in enumerate(row):
                item = QTableWidgetItem(str(data))
                item.setTextAlignment(Qt.AlignCenter)  # 确保文本居中
                self.tableView.setItem(i, j, item)

            # 设置表头
            self.tableView.verticalHeader().hide()
            self.tableView.setHorizontalHeaderLabels(
                ['姓名', '球队', '得分', '篮板', '助攻', '抢断', '盖帽', '失误', '犯规', '正负值', '战力值']
            )
            self.tableView.horizontalHeader().setStyleSheet(
                "QHeaderView::section{background-color:rgb(96, 155, 206);color: white;};"
            )
            self.tableView.setSortingEnabled(True)

            # 固定列宽（避免被自动调整）
            self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)  # 设置所有列为固定模式
            self.tableView.setColumnWidth(0, 170)  # 姓名
            self.tableView.setColumnWidth(1, 80)  # 球队
            self.tableView.setColumnWidth(2, 60)  # 得分
            self.tableView.setColumnWidth(3, 60)  # 篮板
            self.tableView.setColumnWidth(4, 60)  # 助攻
            self.tableView.setColumnWidth(5, 60)  # 抢断
            self.tableView.setColumnWidth(6, 60)  # 盖帽
            self.tableView.setColumnWidth(7, 60)  # 失误
            self.tableView.setColumnWidth(8, 60)  # 犯规
            self.tableView.setColumnWidth(9, 65)  # 正负值
            self.tableView.setColumnWidth(10, 80)  # 战力值

    def on_clicked(self):
        if not self.url:
            self.init_data()
        else:
            self.refresh_table()
        InfoBarWidget.create_success_info_bar(self, "刷新数据", "数据更新成功", 1500, InfoBarPosition.TOP_RIGHT)

    def on_check_score_btn_clicked(self):
        score_text = ""
        for _ in self.team_scores:
            home_team = _["home_team"]
            home_score = _["home_score"]
            away_score = _["away_score"]
            away_team = _["away_team"]
            print(home_team, home_score, away_score, away_team)
            if int(home_score) > int(away_score):
                score_text += '<h3>🏆{} (主) <font color="red">{}</font> - {} {} </h3>'.format(home_team, home_score,
                                                                                              away_score, away_team)
            else:
                score_text += '<h3>{} (主) {} - <font color="red">{}</font> {}🏆 </h3>'.format(home_team, home_score,
                                                                                              away_score, away_team)

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
            self.stateTooltip.setContent('处理完成啦 😆')
            self.stateTooltip.setState(True)
            self.stateTooltip = None
        else:
            self.stateTooltip = StateToolTip('正在处理图片', '请耐心等待哦~~', self)
            self.stateTooltip.move(510, 30)
            self.stateTooltip.show()
