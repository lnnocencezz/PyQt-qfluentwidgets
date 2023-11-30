# coding:utf-8
from PySide2.QtCore import Qt, Signal, QUrl
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QWidget, QFontDialog, QFileDialog
from qfluentwidgets import FluentIcon as FIF, TitleLabel
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, InfoBar, setTheme, isDarkTheme)

from config import cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR


class SettingInterface(ScrollArea):
    """ Setting interface """

    checkUpdateSig = Signal()
    musicFoldersChanged = Signal(list)
    acrylicEnableChanged = Signal(bool)
    downloadFolderChanged = Signal(str)
    minimizeToTrayChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.setObjectName("settingInterface")  # 添加objectName
        # setting label
        self.settingLabel = TitleLabel("设置", self)

        self.downloadFolderCard = PushSettingCard(
            '选择文件夹',
            FIF.DOWNLOAD,
            "下载目录",
            cfg.get(cfg.downloadFolder),
        )

        # personalization
        self.personalGroup = SettingCardGroup('个性化', self.scrollWidget)
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            '应用主题',
            "调整你的应用外观",
            texts=[
                '浅色', '深色', '跟随系统设置'
            ],
            parent=self.personalGroup
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            "界面缩放",
            "调整小部件和字体的大小",
            texts=[
                "100%", "125%", "150%", "175%", "200%", "跟随系统设置"
            ],
            parent=self.personalGroup
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            '语言', '选择界面所使用的的语言',
            texts=['简体中文', '繁體中文', 'English', '跟随系统设置'],
            parent=self.personalGroup
        )

        # main panel
        self.mainPanelGroup = SettingCardGroup('主界面', self.scrollWidget)
        self.minimizeToTrayCard = SwitchSettingCard(
            FIF.MINIMIZE,
            '关闭后最下化到托盘', 'App将继续在后台运行',
            configItem=cfg.minimizeToTray,
            parent=self.mainPanelGroup
        )

        # update software
        self.updateSoftwareGroup = SettingCardGroup("软件更新", self.scrollWidget)
        self.updateOnStartUpCard = SwitchSettingCard(
            FIF.UPDATE,
            '在应用程序启动时检查更新',
            '新版本将更加稳定并拥有更多功能(建议启用此选项)',
            configItem=cfg.checkUpdateAtStartUp,
            parent=self.updateSoftwareGroup
        )

        # application
        self.aboutGroup = SettingCardGroup('关于', self.scrollWidget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            '打开帮助页面',
            FIF.HELP,
            '帮助',
            '发现新功能并了解有关 APP 的使用技巧',
            self.aboutGroup
        )
        self.feedbackCard = PrimaryPushSettingCard(
            text='提供反馈',
            icon=FIF.FEEDBACK,
            title='提供反馈',
            content='通过提供反馈帮助我们改进 APP',
            parent=self.aboutGroup
        )
        self.aboutCard = PrimaryPushSettingCard(
            text='检查更新',
            icon=FIF.INFO,
            title='关于 © ' + '版权所有' + f" {YEAR}, {AUTHOR}. ",
            content='当前版本' + f" {VERSION}",
            parent=self.aboutGroup
        )

        self.init_widget()

    def init_widget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 120, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__set_qss()

        # initialize layout
        self.__init_layout()
        self.__connect_signal_to_slot()

    def __init_layout(self):
        self.settingLabel.move(35, 50)

        # add cards to group
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

        self.updateSoftwareGroup.addSettingCard(self.updateOnStartUpCard)

        self.mainPanelGroup.addSettingCard(self.minimizeToTrayCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.mainPanelGroup)
        self.expandLayout.addWidget(self.updateSoftwareGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __set_qss(self):
        """ set style sheet """
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')

        theme = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{theme}/setting_interface.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def __show_restart_tooltip(self):
        """ show restart tooltip """
        InfoBar.warning(
            '',
            self.tr('Configuration takes effect after restart'),
            parent=self.window()
        )

    def __on_desk_lyric_font_card_clicked(self):
        """ desktop lyric font button clicked slot """
        font, isOk = QFontDialog.getFont(
            cfg.desktopLyricFont, self.window(), self.tr("Choose font"))
        if isOk:
            cfg.desktopLyricFont = font

    def __on_download_folder_card_clicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "../")
        if not folder or cfg.get(cfg.downloadFolder) == folder:
            return

        cfg.set(cfg.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)

    def __on_theme_changed(self, theme: Theme):
        """ theme changed slot """
        # change the theme of qfluentwidgets
        setTheme(theme)

        # chang the theme of setting interface
        self.__set_qss()

    def __connect_signal_to_slot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__show_restart_tooltip)
        cfg.themeChanged.connect(self.__on_theme_changed)

        # music in the pc
        self.downloadFolderCard.clicked.connect(
            self.__on_download_folder_card_clicked)

        # personalization

        # main panel
        self.minimizeToTrayCard.checkedChanged.connect(
            self.minimizeToTrayChanged)

        # about
        self.aboutCard.clicked.connect(self.checkUpdateSig)
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
