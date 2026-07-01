import sys
import subprocess
import webbrowser
import os

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    Theme, setTheme, isDarkTheme, setThemeColor,
    NavigationToolButton, ToolTipFilter, ToolTipPosition,
    SystemThemeListener
)
from qframelesswindow.utils import getSystemAccentColor

from resources.icon import ICON_ICO
from ui.utils.icon_helper import get_icon_from_base64
from ui.tray.tray_manager import TrayManager
from ui.dialogs.close_dialog import CloseConfirmationDialog
from ui.pages.home.home_page import HomePage
from ui.pages.settings.settings_page import SettingsPage
from ui.pages.widget.widget_page import WidgetPage
from ui.pages.data.data_page import DataPage
from ui.pages.storage.storage_page import StoragePage
from ui.services.app_signals import AppSignals
from core.device.device_manager import DeviceManager
from persistence.manager.data_manager import DataManager
from persistence.manager.file_cleaner import FileCleaner
from system.memory.shared_memory import MemoryShareManager
from system.settings.settings_manager import SettingsManager
from system.monitor.system_monitor import SystemMonitor
from system.monitor.storage_service import StorageService


class HeartRateMonitorWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("心率监测器")
        self.resize(900, 700)
        self.setWindowIcon(get_icon_from_base64(ICON_ICO))

        self.tray_manager = TrayManager(get_icon_from_base64(ICON_ICO), self)
        self.tray_manager.set_show_callback(self.show_main_window)
        self.tray_manager.set_exit_callback(self.exit_application)
        self.tray_manager.show()

        self.settings_manager = SettingsManager()
        print("[SettingsManager] 设置管理器已初始化")

        self.data_manager = DataManager()
        print("[DataManager] 数据管理器已初始化")

        self.memory_share = MemoryShareManager()
        self.memory_share.initialize()
        
        self.signals = AppSignals()
        print("[AppSignals] 全局信号已初始化")

        self.device_manager = DeviceManager(
            self.settings_manager, 
            self.data_manager, 
            self.memory_share,
            self.signals
        )
        print("[DeviceManager] 设备管理器已初始化")
        
        self.storage_service = StorageService(self.signals)
        print("[StorageService] 存储服务已初始化")
        
        self.system_monitor = SystemMonitor(self.signals)
        print("[SystemMonitor] 系统监控已初始化")

        if sys.platform in ["win32", "darwin"]:
            try:
                system_color = getSystemAccentColor()
                print(f"[Theme] 获取到的系统主题色: {system_color}")
                setThemeColor(system_color, save=False)
                print(f"[Theme] 已设置主题色为系统色: {system_color}")
            except Exception as e:
                print(f"[Theme] 获取系统主题色失败: {e}")

        setTheme(Theme.LIGHT)
        print("[Theme] 已应用默认主题: 浅色主题")

        self.themeListener = SystemThemeListener(self)
        self.themeListener.start()
        print("[Theme] 系统主题监听器已启动")

        self.initWindow()

        self.homePage = HomePage(self, self.signals, self.device_manager._get_stable_device_name)
        self.addSubInterface(self.homePage, FluentIcon.HOME, "主页")

        self.widgetPage = WidgetPage(self)
        self.addSubInterface(self.widgetPage, FluentIcon.ZOOM, "小组件")

        self.dataPage = DataPage(self)
        self.addSubInterface(self.dataPage, FluentIcon.MARKET, "数据分析与趋势")

        self.storagePage = StoragePage(
            self, 
            self.signals, 
            self.storage_service, 
            self.system_monitor,
            self.settings_manager
        )
        self.addSubInterface(self.storagePage, FluentIcon.SPEED_HIGH, "存储和性能")

        self.websiteButton = NavigationToolButton(FluentIcon.GLOBE, self)
        self.websiteButton.installEventFilter(ToolTipFilter(self.websiteButton, showDelay=300, position=ToolTipPosition.TOP))
        self.websiteButton.setToolTip("官方网站")
        self.websiteButton.clicked.connect(self.on_custom_button_clicked)
        self.navigationInterface.addWidget(
            routeKey='websiteButton',
            widget=self.websiteButton,
            position=NavigationItemPosition.BOTTOM
        )

        self.helpButton = NavigationToolButton(FluentIcon.QUESTION, self)
        self.helpButton.installEventFilter(ToolTipFilter(self.helpButton, showDelay=300, position=ToolTipPosition.TOP))
        self.helpButton.setToolTip("帮助")
        self.helpButton.clicked.connect(self.on_help_button_clicked)
        self.navigationInterface.addWidget(
            routeKey='helpButton',
            widget=self.helpButton,
            position=NavigationItemPosition.BOTTOM
        )

        self.settingsPage = SettingsPage(
            self, 
            self.settings_manager, 
            self.device_manager,
            self.signals,
            self.storage_service
        )
        self.addSubInterface(self.settingsPage, FluentIcon.SETTING, "设置", NavigationItemPosition.BOTTOM)

        # 连接 UI 动作信号 → DeviceManager（HomePage 不再直接引用 DeviceManager）
        self.signals.scan_requested.connect(self.device_manager.start_scan)
        self.signals.connect_requested.connect(self.device_manager.connect_device)
        self.signals.disconnect_requested.connect(self.device_manager.disconnect_device)

        if self.settings_manager.get("auto_clean_on_startup", True):
            print("[AutoClean] 启动时自动清理小文件")
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
            cleaned = FileCleaner.clean_small_files(data_dir)
            if cleaned > 0:
                print(f"[AutoClean] 清理了 {cleaned} 个小文件")
            else:
                print("[AutoClean] 没有需要清理的小文件")

    def initWindow(self):
        window_size = (900, 700)
        self.resize(window_size[0], window_size[1])

        self.setMinimumSize(window_size[0], window_size[1])
        self.setMaximumSize(window_size[0], window_size[1])

        self.setWindowIcon(get_icon_from_base64(ICON_ICO))

        self.setWindowTitle("心率监测器")

        self.titleBar.maxBtn.hide()
        self.titleBar.setDoubleClickEnabled(False)

        self.setMicaEffectEnabled(False)

    def show_main_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_main_window(self):
        self.hide()

    def exit_application(self):
        print("[Cleanup] 开始清理资源")
        try:
            self.themeListener.terminate()
            self.themeListener.deleteLater()
        except RuntimeError:
            pass
        print("[Theme] 系统主题监听器已停止")
        self.data_manager.flush_data()
        print("[DataManager] 数据已保存")
        self.memory_share.close()
        print("[MemoryShare] 共享内存已关闭")
        self.tray_manager.hide()
        QApplication.quit()

    def _onThemeChangedFinish(self):
        super()._onThemeChangedFinish()

        if self.isMicaEffectEnabled():
            QTimer.singleShot(100, lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()))

        print(f"[Theme] 主题已切换为: {'深色' if isDarkTheme() else '浅色'}")

    def on_custom_button_clicked(self):
        webbrowser.open("https://www.nstechcod.top/")

    def on_help_button_clicked(self):
        subprocess.Popen(["python", "helphtml.py"], cwd="d:\\HeartrateReceiver")

    def closeEvent(self, event):
        show_confirmation = self.settings_manager.get("show_close_confirmation", True)
        close_behavior = self.settings_manager.get("close_behavior", "minimize")

        if show_confirmation:
            dialog = CloseConfirmationDialog(self)
            result = dialog.exec()

            if dialog.get_dont_ask_again():
                self.settings_manager.set("show_close_confirmation", False)
                if result == 1:
                    self.settings_manager.set("close_behavior", "minimize")
                elif result == 2:
                    self.settings_manager.set("close_behavior", "close")

            if result == 0:
                event.ignore()
                return
            elif result == 1:
                self.hide_main_window()
                event.ignore()
                return
            elif result == 2:
                self.exit_application()
                event.accept()
                return
        else:
            if close_behavior == "close":
                self.exit_application()
                event.accept()
                return
            else:
                self.hide_main_window()
                event.ignore()
                return
