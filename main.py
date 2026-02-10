import func.startup as startup
startup.go()
# 导入其他模块
import base64
from io import BytesIO
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QWidget
from PyQt5.QtGui import QIcon, QPixmap
from qfluentwidgets import (InfoBar, InfoBarPosition,FluentWindow, NavigationItemPosition,FluentIcon, IconInfoBadge, InfoBadgePosition, Theme, setTheme, isDarkTheme, qconfig, setThemeColor)
# 导入base64编码的图标
from func.icon import ICON_ICO
import sys
# 导入获取系统主题色的函数
from qframelesswindow.utils import getSystemAccentColor

# 从base64数据创建QIcon
def get_icon_from_base64(base64_data):
    """从base64编码数据创建QIcon"""
    try:
        # 解码base64字符串
        icon_data = base64.b64decode(base64_data)
        # 创建BytesIO对象
        icon_stream = BytesIO(icon_data)
        # 创建QPixmap
        pixmap = QPixmap()
        pixmap.loadFromData(icon_stream.getvalue())
        # 创建QIcon
        return QIcon(pixmap)
    except Exception as e:
        print(f"Error creating icon from base64: {e}")
        return QIcon()

from func.core import HeartRateMonitorCore, DeviceScanThread, HeartRateMonitorThread
from func.interfaces import HomeInterface, HeartRateInterface, WidgetsInterface, SettingsInterface
from func.interfaces.heart_rate_window import HeartRateWindow
from func.interfaces.close_confirmation_dialog import CloseConfirmationDialog
from func.settings_manager import SettingsManager
from func.memory_share import MemoryShareManager

# 主窗口类
class HeartRateMonitorWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("心率监测器")
        self.resize(500, 400)
        self.setFixedSize(self.size())
        self.setWindowIcon(get_icon_from_base64(ICON_ICO))
        
        # 初始化设置管理器
        self.settings_manager = SettingsManager()
        
        # 初始化核心功能类
        self.core = HeartRateMonitorCore()
        self.user_disconnecting = False  # 标记用户是否正在主动断开连接
        self.is_disconnecting = False  # 标记是否正在执行断开连接操作，防止重复调用
        # 初始化内存共享管理器
        self.memory_share_manager = MemoryShareManager()
        self.memory_share_manager.initialize()
        
        # 创建界面实例
        self.home_interface = HomeInterface(self)
        self.heart_rate_interface = HeartRateInterface(self, self.settings_manager)
        self.widgets_interface = WidgetsInterface(self)
        self.settings_interface = SettingsInterface(self)
        
        # 添加到导航栏
        self.bluetooth_item = self.addSubInterface(self.home_interface, FluentIcon.BLUETOOTH, "设备连接", NavigationItemPosition.TOP)
        self.addSubInterface(self.heart_rate_interface, FluentIcon.HEART, "心率显示", NavigationItemPosition.TOP)
        self.addSubInterface(self.widgets_interface, FluentIcon.LINK, "小组件", NavigationItemPosition.TOP)
        self.addSubInterface(self.settings_interface, FluentIcon.SETTING, "设置", NavigationItemPosition.TOP)
        
        # 在蓝牙图标上添加 IconInfoBadge，初始为错误状态（红色）
        self.bluetooth_badge = IconInfoBadge.error(FluentIcon.CANCEL_MEDIUM, parent=self, target=self.bluetooth_item, position=InfoBadgePosition.TOP_RIGHT)
        
        # 不需要监听导航栏，直接在SettingsInterface的showEvent中更新设置
        
        # 心率窗口（独立窗口）
        self.heart_rate_window = None
        
        # 初始化系统托盘图标
        self.init_tray_icon()
        
        # 初始化主题设置
        # 1. 获取系统主题色并设置为组件库的主题色
        import sys
        if sys.platform in ["win32", "darwin"]:
            try:
                system_color = getSystemAccentColor()
                print(f"[Theme] 获取到的系统主题色: {system_color}")
                setThemeColor(system_color, save=False)
                print(f"[Theme] 已设置主题色为系统色: {system_color}")
            except Exception as e:
                print(f"[Theme] 获取系统主题色失败: {e}")
        
        # 2. 读取保存的主题设置并应用
        theme = self.settings_manager.get("theme", "light")
        if theme == "light":
            setTheme(Theme.LIGHT)
            print("[Theme] 已应用保存的主题: 浅色主题")
        elif theme == "dark":
            setTheme(Theme.DARK)
            print("[Theme] 已应用保存的主题: 深色主题")
        else:
            # 默认使用浅色主题
            setTheme(Theme.LIGHT)
            print("[Theme] 已应用默认主题: 浅色主题")
        
        # 软件启动时自动执行一次设备扫描
        QTimer.singleShot(600, self.start_scan)
    
    def open_heart_rate_window(self):
        """打开独立的心率显示窗口"""
        if self.heart_rate_window is None:
            self.heart_rate_window = HeartRateWindow(None)
            self.heart_rate_window.parent_window = self
        else:
            # 如果悬浮窗已存在，重新加载设置
            self.heart_rate_window.reload_settings()
        
        self.heart_rate_window.show()
        self.heart_rate_window.raise_()
        self.heart_rate_window.activateWindow()
    
    def close_heart_rate_window(self):
        """关闭独立的心率显示窗口"""
        if self.heart_rate_window:
            self.heart_rate_window.close()
            self.heart_rate_window = None
    
    # 扫描设备
    def start_scan(self):
        self.home_interface.scan_button.setEnabled(False)
        self.home_interface.scan_button.setText("扫描中...")
        # 设置静止进度条颜色为 #009FAA
        from PyQt5.QtGui import QColor
        self.home_interface.progress_bar.setCustomBarColor(QColor(0, 159, 170), QColor(0, 130, 140))
        # 显示不确定进度条，隐藏普通进度条
        self.home_interface.progress_bar.hide()
        self.home_interface.indeterminate_bar.show()
        self.home_interface.indeterminate_bar.start()
        self.core.scan_thread = DeviceScanThread()
        self.core.scan_thread.scan_finished.connect(self.on_scan_finished)
        self.core.scan_thread.scan_error.connect(self.on_scan_error)
        self.core.scan_thread.start()
        
    def on_scan_finished(self, devices):        
        self.core.devices = devices
        self.home_interface.combo_box.clear()
        
        if devices:
            for device in devices:
                device_name = device.name if device.name else "未知设备"
                self.home_interface.combo_box.addItem(f"{device_name} ({device.address})")
            self.home_interface.connect_button.setEnabled(True)
            InfoBar.success(
                title="扫描完成",
                content=f"发现 {len(devices)} 个设备",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            # 扫描完成且找到设备，显示普通进度条（100%），隐藏不确定进度条
            self.home_interface.indeterminate_bar.stop()
            self.home_interface.indeterminate_bar.hide()
            self.home_interface.progress_bar.setValue(100)
            # 重置进度条颜色为默认颜色
            self.home_interface.progress_bar.show()
        else:
            self.home_interface.connect_button.setEnabled(False)
            InfoBar.warning(
                title="未发现设备",
                content="没有扫描到任何设备",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            # 扫描完成但未发现设备，显示暗红色普通进度条，隐藏不确定进度条
            self.home_interface.indeterminate_bar.stop()
            self.home_interface.indeterminate_bar.hide()
            self.home_interface.progress_bar.setValue(100)
            # 设置错误状态颜色为暗红色 C42B1C
            from PyQt5.QtGui import QColor
            self.home_interface.progress_bar.setCustomBarColor(QColor(196, 43, 28), QColor(160, 30, 15))
            self.home_interface.progress_bar.show()
        
        self.home_interface.scan_button.setEnabled(True)
        self.home_interface.scan_button.setText("重新扫描")
        
    def on_scan_error(self, error):
        # 扫描出错，显示暗红色普通进度条，隐藏不确定进度条
        self.home_interface.indeterminate_bar.stop()
        self.home_interface.indeterminate_bar.hide()
        self.home_interface.progress_bar.setValue(100)
        # 设置错误状态颜色为暗红色 C42B1C
        from PyQt5.QtGui import QColor
        self.home_interface.progress_bar.setCustomBarColor(QColor(196, 43, 28), QColor(160, 30, 15))
        self.home_interface.progress_bar.show()
        
        self.home_interface.scan_button.setEnabled(True)
        self.home_interface.scan_button.setText("重新扫描")
        InfoBar.error(
            title="扫描出错：",
            content=f"{error}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
    
    # 连接设备
    def connect_device(self):
        if self.home_interface.combo_box.currentIndex() == -1:
            InfoBar.warning(
                title="请选择设备",
                content="请先选择要连接的设备",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        index = self.home_interface.combo_box.currentIndex()
        self.core.selected_device = self.core.devices[index]
        
        # 检查设备是否支持
        if not self.core.is_device_supported(self.core.selected_device):
            InfoBar.warning(
                title="设备不支持",
                content="请重新选择",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        self.core.monitor_thread = HeartRateMonitorThread(self.core.selected_device)
        self.core.monitor_thread.heart_rate_updated.connect(self.update_heart_rate)
        self.core.monitor_thread.connection_status.connect(self.update_status)
        self.core.monitor_thread.error_occurred.connect(self.on_monitor_error)
        self.core.monitor_thread.start()
        
        self.home_interface.connect_button.setEnabled(False)
        self.home_interface.disconnect_button.setEnabled(True)
        self.home_interface.scan_button.setEnabled(False)
        
        # 自动切换到心率显示界面
        self.stackedWidget.setCurrentWidget(self.heart_rate_interface)

    def on_monitor_error(self, error):
        # 如果是用户主动断开连接，不显示提示
        if not self.user_disconnecting:
            InfoBar.info(
                title="设备已断开",
                content="设备连接已断开，您可以重新扫描或连接其他设备",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self
            )
        self.disconnect_device()
    
    # 更新心率数值
    def update_heart_rate(self, heart_rate):
        self.heart_rate_interface.update_heart_rate(heart_rate)
        if self.heart_rate_window:
            self.heart_rate_window.update_heart_rate(heart_rate)

        # 更新共享内存的心率数据
        self.memory_share_manager.update_heart_rate(heart_rate)

    # 更新状态信息
    def update_status(self, status):
        # 同时更新两个界面的状态显示
        self.heart_rate_interface.update_status(status)
        if self.heart_rate_window:
            self.heart_rate_window.update_status(status)
        
        # 根据连接状态更新蓝牙图标徽章
        if "设备连接成功" in status:
            # 设备连接成功，显示绿色徽章和成功图标
            self.bluetooth_badge.hide()
            self.bluetooth_badge = IconInfoBadge.success(FluentIcon.ACCEPT_MEDIUM, parent=self, target=self.bluetooth_item, position=InfoBadgePosition.TOP_RIGHT)
            self.bluetooth_badge.show()
        elif "已断开连接" in status or "请先连接设备" in status:
            # 设备断开连接，显示红色徽章和错误图标
            self.bluetooth_badge.hide()
            self.bluetooth_badge = IconInfoBadge.error(FluentIcon.CANCEL_MEDIUM, parent=self, target=self.bluetooth_item, position=InfoBadgePosition.TOP_RIGHT)
            self.bluetooth_badge.show()
    
    # 断开设备
    def disconnect_device(self):
        print(f"[DEBUG] disconnect_device called, is_disconnecting: {self.is_disconnecting}, user_disconnecting: {self.user_disconnecting}")
        
        # 如果正在执行断开连接操作，直接返回，避免重复调用
        if self.is_disconnecting:
            print("[DEBUG] Already disconnecting, skipping")
            return
        
        # 如果已经断开连接且没有正在断开，直接返回
        if not self.core.monitor_thread and not self.user_disconnecting:
            print("[DEBUG] Already disconnected, skipping")
            return
            
        # 标记为正在断开连接
        self.is_disconnecting = True
        self.user_disconnecting = True
        
        if self.core.monitor_thread:
            self.core.monitor_thread.stop()
            self.core.monitor_thread.wait()
            self.core.monitor_thread = None
        
        self.home_interface.connect_button.setEnabled(True)
        self.home_interface.disconnect_button.setEnabled(False)
        self.home_interface.scan_button.setEnabled(True)
        self.update_status("已断开连接")
        self.update_heart_rate(0)
        
        # 显示友好的断开连接提示
        InfoBar.info(
            title="设备已断开",
            content="设备连接已断开，您可以重新扫描或连接其他设备",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self
        )
        
        # 断开连接后返回设备连接界面
        self.stackedWidget.setCurrentWidget(self.home_interface)
        
        # 重置标志
        self.user_disconnecting = False
        self.is_disconnecting = False
    
    def init_tray_icon(self):
        """初始化系统托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置托盘图标（从base64资源）
        self.tray_icon.setIcon(get_icon_from_base64(ICON_ICO))
        
        # 创建菜单
        self.tray_menu = QMenu(self)
        
        # 添加显示主窗口动作
        self.show_action = QAction("显示主窗口", self)
        self.show_action.triggered.connect(self.show_main_window)
        self.tray_menu.addAction(self.show_action)
        
        # 添加退出动作
        self.exit_action = QAction("退出", self)
        self.exit_action.triggered.connect(self.exit_application)
        self.tray_menu.addAction(self.exit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # 连接托盘图标激活信号
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # 显示托盘图标
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
        # 关闭所有窗口和线程
        if self.heart_rate_window:
            self.close_heart_rate_window()
        
        if self.core.monitor_thread:
            self.core.monitor_thread.stop()
            self.core.monitor_thread.wait()
            self.core.monitor_thread = None
        

        
        # 关闭共享内存
        self.memory_share_manager.close()
        
        # 隐藏托盘图标
        self.tray_icon.hide()
        
        # 退出应用
        QApplication.quit()
    
    def on_tray_icon_activated(self, reason):
        """托盘图标激活事件处理"""
        # 左键点击显示主窗口
        if reason == QSystemTrayIcon.Trigger:
            self.show_main_window()
    
    # 关闭窗口时的处理
    def _onThemeChangedFinished(self):
        """主题变化完成后的处理"""
        super()._onThemeChangedFinished()
        
        # 云母特效启用时需要增加重试机制
        if self.isMicaEffectEnabled():
            QTimer.singleShot(100, lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()))
        
        print(f"[Theme] 主题已切换为: {'深色' if isDarkTheme() else '浅色'}")

    def closeEvent(self, event):
        """重写关闭事件，实现最小化到任务栏的逻辑"""
        # 检查设置
        close_behavior = self.settings_manager.get("close_behavior", "ask")
        show_confirmation = self.settings_manager.get("show_close_confirmation", True)
        
        # 如果设置了不显示确认对话框，直接执行对应操作
        if not show_confirmation:
            if close_behavior == "minimize":
                self.hide_main_window()
                event.ignore()
            elif close_behavior == "close":
                self.exit_application()
            return
        
        # 显示确认对话框
        dialog = CloseConfirmationDialog(self)
        if dialog.exec_():
            option = dialog.get_option()
            dont_ask_again = dialog.get_dont_ask_again()
            
            # 如果选择了下次不再提示，保存设置
            if dont_ask_again:
                self.settings_manager.set("show_close_confirmation", False)
                self.settings_manager.set("close_behavior", option)
            
            # 执行对应操作
            if option == "minimize":
                self.hide_main_window()
                event.ignore()
            elif option == "close":
                self.exit_application()
        else:
            # 用户取消关闭
            event.ignore()
    
def main():
    app = QApplication(sys.argv)
    # 创建并显示主窗口
    window = HeartRateMonitorWindow()
    window.show()
    
    # 关闭系统闪屏
    startup.close_system_splash(startup.syshwnd)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()