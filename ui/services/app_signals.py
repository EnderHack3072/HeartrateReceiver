from PyQt6.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    """全局应用信号"""
    heart_rate_updated = pyqtSignal(int)
    device_connected = pyqtSignal(str)
    device_disconnected = pyqtSignal()
    status_changed = pyqtSignal(str)
