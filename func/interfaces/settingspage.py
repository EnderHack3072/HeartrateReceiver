from PyQt6.QtWidgets import QFrame, QVBoxLayout
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QWheelEvent
from qfluentwidgets import ExpandGroupSettingCard, FluentIcon, PushButton, ComboBox, SwitchButton, IndicatorPosition, PrimaryPushSettingCard, OptionsSettingCard, qconfig, SpinBox, ScrollArea

class ExitSettingCard(ExpandGroupSettingCard):
    def __init__(self, parent=None):
        super().__init__(FluentIcon.POWER_BUTTON, "关闭选项", "在关闭主窗口时的操作，效果等同于关闭弹窗", parent)

        self.autoComboBox = ComboBox()
        self.autoComboBox.addItems(["直接关闭", "最小化到任务栏"])
        self.autoComboBox.setFixedWidth(165)

        # 第三组
        self.lightnessSwitchButton = SwitchButton("否", self, IndicatorPosition.RIGHT)
        self.lightnessSwitchButton.setOnText("是")

        # 调整内部布局
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        # 添加各组到设置卡中
        self.addGroup(FluentIcon.CLOSE, "关闭行为", "", self.autoComboBox)
        self.addGroup(FluentIcon.QUESTION, "询问是否退出", "", self.lightnessSwitchButton)
    
    def wheelEvent(self, event: QWheelEvent):
        # 将滚轮事件传递给父组件，使其可以滚动
        event.ignore()

class FWSettingCard(ExpandGroupSettingCard):
    def __init__(self, parent=None):
        super().__init__(FluentIcon.ZOOM, "悬浮窗", "设置悬浮窗的行为", parent)

        self.canBePlaced = SwitchButton("禁用", self, IndicatorPosition.RIGHT)
        self.canBePlaced.setOnText("启用")

        self.howToPlace = ComboBox()
        self.howToPlace.addItems(["单击拖动", "双击拖动"])
        self.howToPlace.setFixedWidth(135)

        # 第三组
        self.lightnessSwitchButton = SwitchButton("否", self, IndicatorPosition.RIGHT)
        self.lightnessSwitchButton.setOnText("是")

        # 调整内部布局
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        # 添加各组到设置卡中
        self.addGroup(FluentIcon.RINGER, "是否可拖动", "", self.canBePlaced)
        self.addGroup(FluentIcon.BRIGHTNESS, "拖动方式", "", self.howToPlace)
        self.addGroup(FluentIcon.BRIGHTNESS, "始终置顶", "", self.lightnessSwitchButton)
    
    def wheelEvent(self, event: QWheelEvent):
        # 将滚轮事件传递给父组件，使其可以滚动
        event.ignore()

class CustomSettingCard(ExpandGroupSettingCard):
    def __init__(self, parent=None):
        super().__init__(FluentIcon.SETTING, "自动重连", "决定在连接丢失时的行为", parent)

        self.switchButton = SwitchButton("否", self, IndicatorPosition.RIGHT)
        self.switchButton.setOnText("是")

        self.spinBox1 = SpinBox()
        self.spinBox1.setRange(1, 10)
        self.spinBox1.setValue(5)

        self.spinBox2 = SpinBox()
        self.spinBox2.setRange(3, 10)
        self.spinBox2.setValue(5)

        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        self.addGroup(FluentIcon.POWER_BUTTON, "启用自动重连", "", self.switchButton)
        self.addGroup(FluentIcon.SCROLL, "尝试次数", "", self.spinBox1)
        self.addGroup(FluentIcon.SCROLL, "重连间隔", "", self.spinBox2)
    
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class SettingsPage(QFrame):
    """设置页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        
        # 创建滚动区域（使用QFluentWidgets的ScrollArea，自带fluent风格滚动条）
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # 设置滚动区域背景为透明，与整体界面融合
        self.scrollArea.setStyleSheet("border: none; background-color: transparent;")
        
        # 创建内容框架
        self.frame = QFrame(self.scrollArea)
        self.frame.setStyleSheet("background-color: transparent;")
        self.frameLayout = QVBoxLayout(self.frame)
        self.frameLayout.setSpacing(16)
        # 为右侧滚动条留出空间，避免卡片内容与滚动条重叠
        self.frameLayout.setContentsMargins(0, 0, 20, 0)
        
        # 创建退出设置卡
        self.exitSettingCard = ExitSettingCard(self.frame)
        self.frameLayout.addWidget(self.exitSettingCard)
        
        # 创建悬浮窗设置卡
        self.fwSettingCard = FWSettingCard(self.frame)
        self.frameLayout.addWidget(self.fwSettingCard)
        
        # 添加自定义设置卡
        self.customSettingCard = CustomSettingCard(self.frame)
        self.frameLayout.addWidget(self.customSettingCard)
        
        # 添加主题设置卡
        card = OptionsSettingCard(
             qconfig.themeMode, 
             FluentIcon.BRUSH, 
             "应用主题", 
             "调整你的应用外观", 
             texts=["浅色", "深色", "跟随系统设置"] 
         )
        self.frameLayout.addWidget(card)
        
        # 添加空的PrimaryPushSettingCard
        self.softinfoCard = PrimaryPushSettingCard("检查更新", FluentIcon.INFO, "关于HeartRateReceiver", "2026 EnderHack", self.frame)
        self.frameLayout.addWidget(self.softinfoCard)
        
        # 添加弹性空间
        self.frameLayout.addStretch()
        
        # 将框架设置为滚动区域的 widget
        self.scrollArea.setWidget(self.frame)
        
        # 设置主布局
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(16)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.addWidget(self.scrollArea)
