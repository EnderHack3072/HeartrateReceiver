from PyQt6.QtWidgets import QFrame, QVBoxLayout
from PyQt6.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt6.QtGui import QWheelEvent, QMouseEvent
from qfluentwidgets import ExpandGroupSettingCard, FluentIcon, PushButton, ComboBox, SwitchButton, IndicatorPosition, PrimaryPushSettingCard, OptionsSettingCard, qconfig, SpinBox, ScrollArea, InfoBar, InfoBarPosition
from func.core import check_debug_file

class ExitSettingCard(ExpandGroupSettingCard):
    def __init__(self, settings_manager, parent=None):
        super().__init__(FluentIcon.POWER_BUTTON, "关闭选项", "在关闭主窗口时的操作，效果等同于关闭弹窗", parent)
        self.settings_manager = settings_manager

        self.autoComboBox = ComboBox()
        self.autoComboBox.addItems(["直接关闭", "最小化到任务栏"])
        self.autoComboBox.setFixedWidth(165)
        
        # 加载设置
        close_behavior = self.settings_manager.get("close_behavior", "ask")
        if close_behavior == "close":
            self.autoComboBox.setCurrentIndex(0)
        elif close_behavior == "minimize":
            self.autoComboBox.setCurrentIndex(1)
        
        # 连接信号
        self.autoComboBox.currentIndexChanged.connect(self.on_close_behavior_changed)

        # 第三组
        self.lightnessSwitchButton = SwitchButton("否", self, IndicatorPosition.RIGHT)
        self.lightnessSwitchButton.setOnText("是")
        
        # 加载设置
        show_confirmation = self.settings_manager.get("show_close_confirmation", True)
        self.lightnessSwitchButton.setChecked(show_confirmation)
        
        # 连接信号
        self.lightnessSwitchButton.checkedChanged.connect(self.on_show_confirmation_changed)

        # 调整内部布局
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        # 添加各组到设置卡中
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
        # 将滚轮事件传递给父组件，使其可以滚动
        event.ignore()

class FWSettingCard(ExpandGroupSettingCard):
    def __init__(self, settings_manager, parent=None):
        super().__init__(FluentIcon.ZOOM, "悬浮窗", "设置悬浮窗的行为", parent)
        self.settings_manager = settings_manager

        self.canBePlaced = SwitchButton("禁用", self, IndicatorPosition.RIGHT)
        self.canBePlaced.setOnText("启用")
        
        # 加载设置
        drag_enabled = self.settings_manager.get("floating_window_drag_enabled", True)
        self.canBePlaced.setChecked(drag_enabled)
        
        # 连接信号
        self.canBePlaced.checkedChanged.connect(self.on_drag_enabled_changed)

        self.howToPlace = ComboBox()
        self.howToPlace.addItems(["单击拖动", "双击拖动"])
        self.howToPlace.setFixedWidth(135)
        
        # 加载设置
        drag_type = self.settings_manager.get("floating_window_drag_type", "single_click")
        if drag_type == "single_click":
            self.howToPlace.setCurrentIndex(0)
        else:
            self.howToPlace.setCurrentIndex(1)
        
        # 连接信号
        self.howToPlace.currentIndexChanged.connect(self.on_drag_type_changed)

        # 第三组
        self.lightnessSwitchButton = SwitchButton("否", self, IndicatorPosition.RIGHT)
        self.lightnessSwitchButton.setOnText("是")
        
        # 加载设置
        always_on_top = self.settings_manager.get("floating_window_always_on_top", True)
        self.lightnessSwitchButton.setChecked(always_on_top)
        
        # 连接信号
        self.lightnessSwitchButton.checkedChanged.connect(self.on_always_on_top_changed)

        # 调整内部布局
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        # 添加各组到设置卡中
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
        # 将滚轮事件传递给父组件，使其可以滚动
        event.ignore()

class AutoReconnect(ExpandGroupSettingCard):
    def __init__(self, settings_manager, device_manager=None, parent=None):
        super().__init__(FluentIcon.SETTING, "自动重连", "决定在连接丢失时的行为", parent)
        self.settings_manager = settings_manager
        self.device_manager = device_manager

        self.switchButton = SwitchButton("否", self, IndicatorPosition.RIGHT)
        self.switchButton.setOnText("是")
        
        # 加载设置
        auto_reconnect = self.settings_manager.get("auto_reconnect_enabled", True)
        self.switchButton.setChecked(auto_reconnect)
        
        # 连接信号
        self.switchButton.checkedChanged.connect(self.on_auto_reconnect_changed)

        self.spinBox1 = SpinBox()
        self.spinBox1.setRange(1, 10)
        self.spinBox1.setValue(5)
        
        # 加载设置
        attempts = self.settings_manager.get("auto_reconnect_attempts", 5)
        self.spinBox1.setValue(attempts)
        
        # 连接信号
        self.spinBox1.valueChanged.connect(self.on_attempts_changed)

        self.spinBox2 = SpinBox()
        self.spinBox2.setRange(3, 10)
        self.spinBox2.setValue(5)
        
        # 加载设置
        interval = self.settings_manager.get("auto_reconnect_interval", 5)
        self.spinBox2.setValue(interval)
        
        # 连接信号
        self.spinBox2.valueChanged.connect(self.on_interval_changed)

        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        self.addGroup(FluentIcon.POWER_BUTTON, "启用自动重连", "", self.switchButton)
        self.addGroup(FluentIcon.SCROLL, "尝试次数", "", self.spinBox1)
        self.addGroup(FluentIcon.SCROLL, "重连间隔", "", self.spinBox2)
    
    def on_auto_reconnect_changed(self, checked):
        self.settings_manager.set("auto_reconnect_enabled", checked)
        print(f"[Settings] 自动重连: {'启用' if checked else '禁用'}")
        # 更新 device_manager 中的设置
        if self.device_manager and hasattr(self.device_manager, 'core'):
            self.device_manager.core.auto_reconnect_enabled = checked
            # 重新加载设置
            self.device_manager.core.load_settings()
    
    def on_attempts_changed(self, value):
        self.settings_manager.set("auto_reconnect_attempts", value)
        print(f"[Settings] 重连尝试次数: {value}")
        # 更新 device_manager 中的设置
        if self.device_manager and hasattr(self.device_manager, 'core'):
            self.device_manager.core.max_reconnect_attempts = value
    
    def on_interval_changed(self, value):
        self.settings_manager.set("auto_reconnect_interval", value)
        print(f"[Settings] 重连间隔: {value}秒")
        # 更新 device_manager 中的设置
        if self.device_manager and hasattr(self.device_manager, 'core'):
            self.device_manager.core.reconnect_interval = value
    
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class LocalDataSettingCard(ExpandGroupSettingCard):
    def __init__(self, parent_window, parent=None):
        super().__init__(FluentIcon.FOLDER, "本地数据", "管理本地数据文件", parent)
        self.parent_window = parent_window
        
        self.cleanupButton = PushButton("立即整理", self)
        self.cleanupButton.clicked.connect(self.on_cleanup_clicked)
        
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)
        
        self.addGroup(FluentIcon.CLEAR_SELECTION, "数据文件整理", "删除小于等于10KB的数据文件，保留大于等于10KB的文件", self.cleanupButton)
    
    def on_cleanup_clicked(self):
        """处理文件整理按钮点击事件"""
        if hasattr(self.parent_window, 'parent_window') and hasattr(self.parent_window.parent_window, 'data_manager'):
            data_manager = self.parent_window.parent_window.data_manager
            result = data_manager.clean_up_files()
            
            if result["total"] == 0:
                InfoBar.info(
                    title="整理完成",
                    content="没有找到数据文件",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.parent_window
                )
            else:
                InfoBar.success(
                    title="整理完成",
                    content=f"总共 {result['total']} 个文件，删除 {result['deleted']} 个，保留 {result['kept']} 个",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=4000,
                    parent=self.parent_window
                )
        else:
            InfoBar.error(
                title="功能不可用",
                content="无法访问数据管理器",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.parent_window
            )
    
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class SettingsPage(QFrame):
    """设置页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.parent_window = parent
        self.click_count = 0
        self.click_timer = QTimer()
        self.click_timer.timeout.connect(self.reset_click_count)
        
        # 获取设置管理器
        if hasattr(parent, 'settings_manager'):
            self.settings_manager = parent.settings_manager
        else:
            from func.settings_manager import SettingsManager
            self.settings_manager = SettingsManager()
        
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
        self.exitSettingCard = ExitSettingCard(self.settings_manager, self.frame)
        self.frameLayout.addWidget(self.exitSettingCard)
        
        # 创建悬浮窗设置卡
        self.fwSettingCard = FWSettingCard(self.settings_manager, self.frame)
        self.frameLayout.addWidget(self.fwSettingCard)
        
        # 添加自定义设置卡，传递 device_manager
        device_manager = None
        if hasattr(parent, 'device_manager'):
            device_manager = parent.device_manager
        self.autoReconnectCard = AutoReconnect(self.settings_manager, device_manager, self.frame)
        self.frameLayout.addWidget(self.autoReconnectCard)
        
        # 添加主题设置卡
        card = OptionsSettingCard(
             qconfig.themeMode, 
             FluentIcon.BRUSH, 
             "应用主题", 
             "调整你的应用外观", 
             texts=["浅色", "深色", "跟随系统设置"] 
         )
        card.wheelEvent = self.wheelEvent
        self.frameLayout.addWidget(card)
        
        # 添加本地数据手风琴设置卡
        self.localDataCard = LocalDataSettingCard(self, self.frame)
        self.frameLayout.addWidget(self.localDataCard)
        
        # 添加空的PrimaryPushSettingCard
        self.softinfoCard = PrimaryPushSettingCard("检查更新", FluentIcon.INFO, "关于HeartRateReceiver", "2026 EnderHack", self.frame)
        # 安装事件过滤器以捕获整个卡片的点击事件
        self.softinfoCard.installEventFilter(self)
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
    
    def eventFilter(self, obj, event):
        """事件过滤器，捕获softinfoCard的点击事件"""
        if obj == self.softinfoCard and event.type() == QEvent.Type.MouseButtonRelease:
            self.on_softinfo_card_clicked()
            return True
        return super().eventFilter(obj, event)
    
    def on_softinfo_card_clicked(self):
        """处理softinfoCard的点击事件"""
        # 检查.debug文件是否存在
        if not check_debug_file():
            #InfoBar.warning(
            #    title="测试功能未启用",
            #    content=".debug文件不存在",
            #    orient=Qt.Orientation.Horizontal,
            #    isClosable=True,
            #    position=InfoBarPosition.TOP,
            #    duration=2000,
            #    parent=self
            #)
            return
        
        # 增加点击计数
        self.click_count += 1
        self.click_timer.stop()
        self.click_timer.start(3000)  # 3秒内必须完成7次点击
        
        print(f"[DebugClick] 点击次数: {self.click_count}/7")
        
        if self.click_count >= 7:
            self.click_count = 0
            self.click_timer.stop()
            self.activate_simulator_mode()
    
    def reset_click_count(self):
        """重置点击计数"""
        self.click_count = 0
        print("[DebugClick] 点击计数已重置")
    

    
    def activate_simulator_mode(self):
        """激活模拟模式 - 直接切换到主页并添加模拟设备"""
        if hasattr(self.parent_window, 'switchTo'):
            self.parent_window.switchTo(self.parent_window.homePage)
        
        if hasattr(self.parent_window, 'device_manager'):
            device_manager = self.parent_window.device_manager
            device_manager.simulator_activated = True  # 标记为已激活
            if not device_manager.simulator_mode:
                # 检查设备列表中是否已经有模拟设备
                list_widget = self.parent_window.homePage.listWidget
                has_simulator = False
                for i in range(list_widget.count()):
                    if list_widget.item(i).text() == "模拟心率设备 (Debug)":
                        has_simulator = True
                        break
                
                if not has_simulator:
                    device_manager._add_simulator_device()
                
                InfoBar.success(
                    title="模拟设备已就绪",
                    content="请在设备列表中选择「模拟心率设备 (Debug)」并点击连接",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=4000,
                    parent=self
                )
            else:
                device_manager.stop_simulator()
        else:
            InfoBar.error(
                title="功能不可用",
                content="无法访问设备管理器",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
