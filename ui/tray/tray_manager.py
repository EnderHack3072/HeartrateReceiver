from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction


class TrayManager:
    """系统托盘管理器"""

    def __init__(self, icon, parent=None):
        self.tray_icon = QSystemTrayIcon(parent)
        self.tray_icon.setIcon(icon)

        self.tray_menu = QMenu(parent)

        self.show_action = QAction("显示主窗口", parent)
        self.exit_action = QAction("退出", parent)

        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._on_activated)

        self._double_click_callback = None

    def set_show_callback(self, callback):
        self.show_action.triggered.connect(callback)
        self._double_click_callback = callback

    def set_exit_callback(self, callback):
        self.exit_action.triggered.connect(callback)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._double_click_callback:
                self._double_click_callback()

    def show(self):
        self.tray_icon.show()

    def hide(self):
        self.tray_icon.hide()
