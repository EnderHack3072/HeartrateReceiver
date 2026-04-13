from PyQt6.QtWidgets import QFrame, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent
from qfluentwidgets import ExpandGroupSettingCard, FluentIcon, ComboBox, SwitchButton, IndicatorPosition, PrimaryPushSettingCard, OptionsSettingCard, qconfig, SpinBox, ScrollArea

class ExitSettingCard(ExpandGroupSettingCard):
    def __init__(self, settings_manager, parent=None):
        super().__init__(FluentIcon.POWER_BUTTON, "关闭选项", "在关闭主窗口时的操作，效果等同于关闭弹窗", parent)
        self.settings_manager = settings_manager

        self.autoComboBox = ComboBox()
        self.autoComboBox.addItems(["直接关闭", "最小化到任务栏"])
        self.autoComboBox.setFixedWidth(165)
        
        close_behavior = self.settings_manager.get("close_behavior", "minimize")
        if close_behavior == "close":
            self.autoComboBox.setCurrentIndex(0)
        else:
            self.autoComboBox.setCurrentIndex(1)
        
        self.autoComboBox.currentIndexChanged.connect(self.on_close_behavior_changed)

        self.lightnessSwitchButton = SwitchButton("否", self, IndicatorPosition.RIGHT)
        self.lightnessSwitchButton.setOnText("是")
        
        show_confirmation = self.settings_manager.get("show_close_confirmation", True)
        self.lightnessSwitchButton.setChecked(show_confirmation)
        
        self.lightnessSwitchButton.checkedChanged.connect(self.on_show_confirmation_changed)

        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        self.addGroup(FluentIcon.CLOSE, "关闭行为", "", self.autoComboBox)
        self.addGroup(FluentIcon.QUESTION, "询问是否退出", "", self.lightnessSwitchButton)
    
    def on_close_behavior_changed(self, index):
        behavior = "close" if index == 0 else "minimize"
        self.settings_manager.set("close_behavior", behavior)
        print(f"[Settings] 关闭行为已设置为: {behavior}")
    
    def on_show_confirmation_changed(self, checked):
        self.settings_manager.set("show_close_confirmation", checked)
        print(f"[Settings] 显示关闭确认: {checked}")
    
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class FWSettingCard(ExpandGroupSettingCard):
    def __init__(self, settings_manager, parent=None):
        super().__init__(FluentIcon.ZOOM, "悬浮窗", "设置悬浮窗的行为", parent)
        self.settings_manager = settings_manager

        self.canBePlaced = SwitchButton("禁用", self, IndicatorPosition.RIGHT)
        self.canBePlaced.setOnText("启用")
        
        drag_enabled = self.settings_manager.get("floating_window_drag_enabled", True)
        self.canBePlaced.setChecked(drag_enabled)
        
        self.canBePlaced.checkedChanged.connect(self.on_drag_enabled_changed)

        self.howToPlace = ComboBox()
        self.howToPlace.addItems(["单击拖动", "双击拖动"])
        self.howToPlace.setFixedWidth(135)
        
        drag_type = self.settings_manager.get("floating_window_drag_type", "single_click")
        if drag_type == "single_click":
            self.howToPlace.setCurrentIndex(0)
        else:
            self.howToPlace.setCurrentIndex(1)
        
        self.howToPlace.currentIndexChanged.connect(self.on_drag_type_changed)

        self.lightnessSwitchButton = SwitchButton("否", self, IndicatorPosition.RIGHT)
        self.lightnessSwitchButton.setOnText("是")
        
        always_on_top = self.settings_manager.get("floating_window_always_on_top", True)
        self.lightnessSwitchButton.setChecked(always_on_top)
        
        self.lightnessSwitchButton.checkedChanged.connect(self.on_always_on_top_changed)

        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        self.addGroup(FluentIcon.RINGER, "是否可拖动", "", self.canBePlaced)
        self.addGroup(FluentIcon.BRIGHTNESS, "拖动方式", "", self.howToPlace)
        self.addGroup(FluentIcon.BRIGHTNESS, "始终置顶", "", self.lightnessSwitchButton)
    
    def on_drag_enabled_changed(self, checked):
        self.settings_manager.set("floating_window_drag_enabled", checked)
        print(f"[Settings] 悬浮窗拖动: {'启用' if checked else '禁用'}")
    
    def on_drag_type_changed(self, index):
        drag_type = "single_click" if index == 0 else "double_click"
        self.settings_manager.set("floating_window_drag_type", drag_type)
        print(f"[Settings] 拖动方式: {drag_type}")
    
    def on_always_on_top_changed(self, checked):
        self.settings_manager.set("floating_window_always_on_top", checked)
        print(f"[Settings] 始终置顶: {checked}")
    
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class AutoReconnect(ExpandGroupSettingCard):
    def __init__(self, settings_manager, device_manager=None, parent=None):
        super().__init__(FluentIcon.SETTING, "自动重连", "决定在连接丢失时的行为", parent)
        self.settings_manager = settings_manager
        self.device_manager = device_manager

        self.switchButton = SwitchButton("否", self, IndicatorPosition.RIGHT)
        self.switchButton.setOnText("是")
        
        auto_reconnect = self.settings_manager.get("auto_reconnect_enabled", True)
        self.switchButton.setChecked(auto_reconnect)
        
        self.switchButton.checkedChanged.connect(self.on_auto_reconnect_changed)

        self.spinBox1 = SpinBox()
        self.spinBox1.setRange(1, 10)
        self.spinBox1.setValue(5)
        
        attempts = self.settings_manager.get("auto_reconnect_attempts", 5)
        self.spinBox1.setValue(attempts)
        
        self.spinBox1.valueChanged.connect(self.on_attempts_changed)

        self.spinBox2 = SpinBox()
        self.spinBox2.setRange(3, 10)
        self.spinBox2.setValue(5)
        
        interval = self.settings_manager.get("auto_reconnect_interval", 5)
        self.spinBox2.setValue(interval)
        
        self.spinBox2.valueChanged.connect(self.on_interval_changed)

        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        self.addGroup(FluentIcon.POWER_BUTTON, "启用自动重连", "", self.switchButton)
        self.addGroup(FluentIcon.SCROLL, "尝试次数", "", self.spinBox1)
        self.addGroup(FluentIcon.SCROLL, "重连间隔", "", self.spinBox2)
    
    def on_auto_reconnect_changed(self, checked):
        self.settings_manager.set("auto_reconnect_enabled", checked)
        print(f"[Settings] 自动重连: {'启用' if checked else '禁用'}")
        if self.device_manager and hasattr(self.device_manager, 'core'):
            self.device_manager.core.auto_reconnect_enabled = checked
            self.device_manager.core.load_settings()
    
    def on_attempts_changed(self, value):
        self.settings_manager.set("auto_reconnect_attempts", value)
        print(f"[Settings] 重连尝试次数: {value}")
        if self.device_manager and hasattr(self.device_manager, 'core'):
            self.device_manager.core.max_reconnect_attempts = value
    
    def on_interval_changed(self, value):
        self.settings_manager.set("auto_reconnect_interval", value)
        print(f"[Settings] 重连间隔: {value}秒")
        if self.device_manager and hasattr(self.device_manager, 'core'):
            self.device_manager.core.reconnect_interval = value
    
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class StorageSettingCard(ExpandGroupSettingCard):
    def __init__(self, settings_manager, parent=None):
        super().__init__(FluentIcon.FOLDER, "存储设置", "设置存储相关的选项", parent)
        self.settings_manager = settings_manager

        self.autoCleanSwitchButton = SwitchButton("否", self, IndicatorPosition.RIGHT)
        self.autoCleanSwitchButton.setOnText("是")
        
        auto_clean = self.settings_manager.get("auto_clean_on_startup", True)
        self.autoCleanSwitchButton.setChecked(auto_clean)
        
        self.autoCleanSwitchButton.checkedChanged.connect(self.on_auto_clean_changed)

        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        self.addGroup(FluentIcon.TRANSPARENT, "每次启动时检查并清理", "启动时自动清理小于5KB的文件（最新文件除外）", self.autoCleanSwitchButton)
    
    def on_auto_clean_changed(self, checked):
        self.settings_manager.set("auto_clean_on_startup", checked)
        print(f"[Settings] 每次启动时检查并清理: {'启用' if checked else '禁用'}")
    
    def wheelEvent(self, event):
        event.ignore()

class SettingsPage(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.parent_window = parent
        
        if hasattr(parent, 'settings_manager'):
            self.settings_manager = parent.settings_manager
        else:
            from func.settings_manager import SettingsManager
            self.settings_manager = SettingsManager()
        
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollArea.setStyleSheet("border: none; background-color: transparent;")
        
        self.frame = QFrame(self.scrollArea)
        self.frame.setStyleSheet("background-color: transparent;")
        self.frameLayout = QVBoxLayout(self.frame)
        self.frameLayout.setSpacing(16)
        self.frameLayout.setContentsMargins(0, 0, 20, 0)
        
        self.exitSettingCard = ExitSettingCard(self.settings_manager, self.frame)
        self.frameLayout.addWidget(self.exitSettingCard)
        
        self.fwSettingCard = FWSettingCard(self.settings_manager, self.frame)
        self.frameLayout.addWidget(self.fwSettingCard)
        
        device_manager = None
        if hasattr(parent, 'device_manager'):
            device_manager = parent.device_manager
        self.autoReconnectCard = AutoReconnect(self.settings_manager, device_manager, self.frame)
        self.frameLayout.addWidget(self.autoReconnectCard)
        
        self.storageSettingCard = StorageSettingCard(self.settings_manager, self.frame)
        self.frameLayout.addWidget(self.storageSettingCard)
        
        card = OptionsSettingCard(
             qconfig.themeMode, 
             FluentIcon.BRUSH, 
             "应用主题", 
             "调整你的应用外观", 
             texts=["浅色", "深色", "跟随系统设置"] 
         )
        card.wheelEvent = self.wheelEvent
        self.frameLayout.addWidget(card)
        
        self.softinfoCard = PrimaryPushSettingCard("检查更新", FluentIcon.INFO, "关于HeartRateReceiver", "2026 EnderHack", self.frame)
        self.frameLayout.addWidget(self.softinfoCard)
        
        self.frameLayout.addStretch()
        
        self.scrollArea.setWidget(self.frame)
        
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(16)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.addWidget(self.scrollArea)
