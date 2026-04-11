import func.startup as startup
startup.go()
import base64
from io import BytesIO
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QAction
from qfluentwidgets import (InfoBar, InfoBarPosition, FluentWindow, NavigationItemPosition, FluentIcon, IconInfoBadge, InfoBadgePosition, Theme, setTheme, isDarkTheme, qconfig, setThemeColor, MessageBoxBase, SubtitleLabel, PushButton, CheckBox, PrimaryPushButton, ToolTipFilter, ToolTipPosition)
from func.icon import ICON_ICO
import sys
from qframelesswindow.utils import getSystemAccentColor
from func.device_manager import DeviceManager
from func.data_manager import DataManager
from func.memory_share import MemoryShareManager
from func.settings_manager import SettingsManager

def get_icon_from_base64(base64_data):
    """从base64编码数据创建QIcon"""
    try:
        icon_data = base64.b64decode(base64_data)
        icon_stream = BytesIO(icon_data)
        pixmap = QPixmap()
        pixmap.loadFromData(icon_stream.getvalue())
        return QIcon(pixmap)
    except Exception as e:
        print(f"Error creating icon from base64: {e}")
        return QIcon()

class CloseConfirmationDialog(MessageBoxBase):
    """关闭确认对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.titleLabel = SubtitleLabel("关闭确认", self)
        self.viewLayout.addWidget(self.titleLabel)
        
        self.messageLabel = SubtitleLabel("您确定要关闭应用程序吗？", self)
        self.messageLabel.setStyleSheet("font-size: 14px; font-weight: normal;")
        self.viewLayout.addWidget(self.messageLabel)
        
        self.dontAskAgainCheckBox = CheckBox("以后不再提示", self)
        self.viewLayout.addWidget(self.dontAskAgainCheckBox)
        
        self.hideYesButton()
        self.hideCancelButton()
        
        self.minimizeButton = PushButton("最小化到任务栏", self)
        self.exitButton = PrimaryPushButton("退出", self)
        
        self.buttonLayout.addWidget(self.minimizeButton)
        self.buttonLayout.addWidget(self.exitButton)
        
        self.minimizeButton.clicked.connect(self.accept)
        self.exitButton.clicked.connect(lambda: self.done(2))
        
        self.widget.setMinimumWidth(350)
    
    def get_dont_ask_again(self):
        """获取是否不再提示的状态"""
        return self.dontAskAgainCheckBox.isChecked()
        
from func.interfaces.mainpage import HomePage
from func.interfaces.settingspage import SettingsPage
from func.interfaces.widgetpage import WidgetPage
from func.interfaces.datapage import DataPage
from func.interfaces.storagepage import StoragePage

class HeartRateMonitorWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("心率监测器")
        self.resize(900, 700)
        self.setWindowIcon(get_icon_from_base64(ICON_ICO))
        
        self.init_tray_icon()
        
        self.settings_manager = SettingsManager()
        print("[SettingsManager] 设置管理器已初始化")
        
        self.data_manager = DataManager()
        print("[DataManager] 数据管理器已初始化")
        
        self.memory_share = MemoryShareManager()
        self.memory_share.initialize()
        
        self.device_manager = DeviceManager(self)
        
        import sys
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
        
        self.initWindow()
        
        self.homePage = HomePage(self)
        self.addSubInterface(self.homePage, FluentIcon.HOME, "主页")
        
        self.widgetPage = WidgetPage(self)
        self.addSubInterface(self.widgetPage, FluentIcon.ZOOM, "小组件")
        
        self.dataPage = DataPage(self)
        self.addSubInterface(self.dataPage, FluentIcon.MARKET, "数据")
        
        self.storagePage = StoragePage(self)
        self.addSubInterface(self.storagePage, FluentIcon.FOLDER, "存储")

        from qfluentwidgets import NavigationToolButton
        self.websiteButton = NavigationToolButton(FluentIcon.GLOBE, self)
        self.websiteButton.installEventFilter(ToolTipFilter(self.websiteButton, showDelay=300, position=ToolTipPosition.TOP))
        self.websiteButton.setToolTip("官方网站")
        self.websiteButton.clicked.connect(self.on_custom_button_clicked)
        self.navigationInterface.addWidget(
            routeKey='websiteButton',
            widget=self.websiteButton,
            position=NavigationItemPosition.BOTTOM
        )
        
        self.settingsPage = SettingsPage(self)
        self.addSubInterface(self.settingsPage, FluentIcon.SETTING, "设置", NavigationItemPosition.BOTTOM)
        
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication
        QTimer.singleShot(600, self.device_manager.start_scan)
    
    
    def initWindow(self):
        """初始化窗口"""
        window_size = (900, 700)
        self.resize(window_size[0], window_size[1])
        
        self.setMinimumSize(window_size[0], window_size[1])
        self.setMaximumSize(window_size[0], window_size[1])
        
        self.setWindowIcon(get_icon_from_base64(ICON_ICO))
        
        self.setWindowTitle("心率监测器")
        
        self.titleBar.maxBtn.hide()
        self.titleBar.setDoubleClickEnabled(False)
        
        self.setMicaEffectEnabled(True)
        
    
    def init_tray_icon(self):
        """初始化系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        
        self.tray_icon.setIcon(get_icon_from_base64(ICON_ICO))
        
        self.tray_menu = QMenu(self)
        
        self.show_action = QAction("显示主窗口", self)
        self.show_action.triggered.connect(self.show_main_window)
        self.tray_menu.addAction(self.show_action)
        
        self.exit_action = QAction("退出", self)
        self.exit_action.triggered.connect(self.exit_application)
        self.tray_menu.addAction(self.exit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        self.tray_icon.show()
    
    def show_main_window(self):
        """显示主窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def hide_main_window(self):
        """隐藏主窗口"""
        self.hide()
    
    def exit_application(self):
        """退出应用程序"""
        print("[Cleanup] 开始清理资源")
        self.data_manager.flush_data()
        print("[DataManager] 数据已保存")
        self.memory_share.close()
        print("[MemoryShare] 共享内存已关闭")
        self.tray_icon.hide()
        QApplication.quit()
    
    def on_tray_icon_activated(self, reason):
        """托盘图标激活事件处理"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_main_window()
    
    def _onThemeChangedFinish(self):
        """主题变化完成后的处理"""
        super()._onThemeChangedFinish()
        
        if self.isMicaEffectEnabled():
            QTimer.singleShot(100, lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()))
        
        print(f"[Theme] 主题已切换为: {'深色' if isDarkTheme() else '浅色'}")
    
    def connect_device(self):
        self.device_manager.connect_device()
    
    def disconnect_device(self):
        self.device_manager.disconnect_device()
    
    def on_custom_button_clicked(self):
        """自定义按钮点击事件处理"""
        import webbrowser
        webbrowser.open("https://www.nstechcod.top/")
    
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
    
def main():
    app = QApplication(sys.argv)
    window = HeartRateMonitorWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()