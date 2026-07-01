from PyQt6.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    """全局应用信号 - 用于 UI 和逻辑层解耦"""

    # 心率相关
    heart_rate_updated = pyqtSignal(int)
    heart_rate_stats_updated = pyqtSignal(int, int)  # max, min

    # 设备扫描相关
    scan_started = pyqtSignal()
    scan_finished = pyqtSignal(list)
    scan_failed = pyqtSignal(str)
    device_found = pyqtSignal(object)  # DeviceInfo
    device_updated = pyqtSignal(object)
    device_list_cleared = pyqtSignal()

    # 设备连接相关
    device_connecting = pyqtSignal()
    device_connected = pyqtSignal(str)  # device name
    device_disconnected = pyqtSignal()
    connection_status_changed = pyqtSignal(str)
    connection_error = pyqtSignal(str)

    # UI → 逻辑 动作信号 (HomePage 触发, MainWindow 中介, DeviceManager 响应)
    scan_requested = pyqtSignal(bool)     # filter_heart_rate_devices
    connect_requested = pyqtSignal(str)   # selected device text
    disconnect_requested = pyqtSignal()

    # UI 状态控制信号 (DeviceManager → UI)
    ui_scan_state_changed = pyqtSignal(bool, str)  # enabled, text
    ui_progress_state_changed = pyqtSignal(bool, bool)  # indeterminate visible, progress visible
    ui_connect_state_changed = pyqtSignal(bool, bool)  # connect enabled, disconnect enabled
    ui_list_enabled_changed = pyqtSignal(bool)
    ui_checkbox_enabled_changed = pyqtSignal(bool)

    # 通知/提示
    info_bar_requested = pyqtSignal(str, str, str)  # type (info, warn, error, success), title, content

    # 系统监控 (CPU/内存)
    cpu_info_updated = pyqtSignal(float, float, float)
    memory_info_updated = pyqtSignal(int, int, float, int, float, float)

    # 磁盘/存储
    disk_space_updated = pyqtSignal(float, float, float)  # total_gb, used_gb, percent
    file_list_updated = pyqtSignal(list, int, str, int)  # files, count, size_str, small_files_count

    # 设置变更
    settings_changed = pyqtSignal(str, object)
