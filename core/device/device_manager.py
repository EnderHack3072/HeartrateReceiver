import threading
from core.ble.scanner import DeviceScanThread, DeviceInfo
from core.ble.monitor import HeartRateMonitorThread
from core.device.heart_rate_core import HeartRateMonitorCore


class DeviceManager:
    def __init__(self, settings_manager, data_manager, memory_share, signals):
        self.settings_manager = settings_manager
        self.data_manager = data_manager
        self.memory_share = memory_share
        self.signals = signals

        self.core = HeartRateMonitorCore(settings_manager)
        self.user_disconnecting = False
        self.is_disconnecting = False

        self.discovered_devices = {}
        self.MAX_DEVICES = 100

        # threading.Timer 替代 QTimer
        self.reconnect_timer = None

        self._first_heart_rate_received = False

    def _cancel_reconnect_timer(self):
        if self.reconnect_timer:
            self.reconnect_timer.cancel()
            self.reconnect_timer = None

    def start_scan(self, filter_heart_rate_devices=True):
        self.discovered_devices.clear()
        self.core.devices = []

        self.signals.device_list_cleared.emit()
        self.signals.scan_started.emit()
        self.signals.ui_scan_state_changed.emit(False, "扫描中...")
        self.signals.ui_progress_state_changed.emit(True, False)

        self.core.scan_thread = DeviceScanThread(
            on_scan_started=self._on_scan_started,
            on_scan_finished=self.on_scan_finished,
            on_scan_error=self.on_scan_error,
            on_device_found=self._on_device_found,
            on_device_updated=self._on_device_updated,
            filter_heart_rate_devices=filter_heart_rate_devices
        )
        self.core.scan_thread.start()

    def _on_scan_started(self):
        print("[DeviceManager] 扫描已开始")

    def _get_device_display_text(self, address, name):
        if name and name.strip():
            return name
        else:
            return address

    def _on_device_found(self, device_info):
        address = device_info.address

        if address in self.discovered_devices:
            return

        if len(self.discovered_devices) >= self.MAX_DEVICES:
            print(f"[DeviceManager] 已达到最大设备数量限制 {self.MAX_DEVICES}")
            return

        self.discovered_devices[address] = device_info

        # 回调来自后台线程，Qt 信号发射是线程安全的（自动 queued）
        self.signals.device_found.emit(device_info)

        print(f"[DeviceManager] 添加设备到列表: {self._get_device_display_text(address, self._get_stable_device_name(address, device_info.name))}")

    def _on_device_updated(self, device_info):
        address = device_info.address

        if address not in self.discovered_devices:
            return

        self.discovered_devices[address] = device_info

        self.signals.device_updated.emit(device_info)

    def _get_stable_device_name(self, address, current_name):
        valid_name = current_name if current_name and current_name.strip() and current_name != "未知设备" else None
        cached_name = self.settings_manager.get_device_name(address)

        if cached_name:
            if valid_name and valid_name != cached_name:
                print(f"[DeviceManager] 更新稳定名称: {address}: {cached_name} -> {valid_name}")
                self.settings_manager.set_device_name(address, valid_name)
                return valid_name
            return cached_name
        else:
            if valid_name:
                self.settings_manager.set_device_name(address, valid_name)
                return valid_name
            return None

    def on_scan_finished(self, devices):
        self.core.devices = devices

        if self.discovered_devices:
            self._finish_scan_ui(success=True)
        else:
            self.signals.info_bar_requested.emit("warn", "未发现设备", "没有扫描到任何设备")
            self._finish_scan_ui(success=False)

    def _finish_scan_ui(self, success):
        self.signals.ui_progress_state_changed.emit(False, True)

        if not success:
            self.signals.info_bar_requested.emit("error", "扫描完成", "没有找到设备")

        if self.core.monitor_thread and self.core.monitor_thread.is_alive():
            return

        self.signals.ui_scan_state_changed.emit(True, "重新扫描")

    def on_scan_error(self, error):
        self.signals.ui_progress_state_changed.emit(False, True)

        if self.core.monitor_thread and self.core.monitor_thread.is_alive():
            return

        self.signals.ui_scan_state_changed.emit(True, "重新扫描")
        self.signals.info_bar_requested.emit("error", "扫描出错", f"{error}")

    def stop_scan(self):
        if self.core.scan_thread and self.core.scan_thread.is_alive():
            self.core.scan_thread.stop()
            self.core.scan_thread.join(timeout=3)
            self.core.scan_thread = None

            self.signals.ui_progress_state_changed.emit(False, True)

    def connect_device(self, selected_text):
        self._first_heart_rate_received = False

        if not selected_text:
            self.signals.info_bar_requested.emit("warn", "请选择设备", "请先选择要连接的设备")
            return

        selected_info = None
        device_list = list(self.discovered_devices.values())

        for info in device_list:
            display_name = self._get_stable_device_name(info.address, info.name)
            display_text = self._get_device_display_text(info.address, display_name)
            if display_text == selected_text:
                selected_info = info
                break

        if not selected_info:
            self.signals.info_bar_requested.emit("warn", "设备选择错误", "请重新选择设备")
            return

        self.core.selected_device = selected_info.device
        self.core.devices = device_list

        if not self.core.is_device_supported(self.core.selected_device):
            self.signals.info_bar_requested.emit("warn", "设备不支持", "请重新选择")
            return

        self.stop_scan()

        if self.core.monitor_thread:
            self.core.monitor_thread.stop()
            self.core.monitor_thread.join(timeout=3)
            self.core.monitor_thread = None

        self.core.monitor_thread = HeartRateMonitorThread(
            self.core.selected_device,
            on_heart_rate_updated=self.update_heart_rate,
            on_connection_status=self.update_status,
            on_error=self.on_monitor_error
        )
        self.core.monitor_thread.start()

        self.signals.ui_connect_state_changed.emit(False, True)
        self.signals.ui_scan_state_changed.emit(False, "设备已连接，请先断开")
        self.signals.ui_checkbox_enabled_changed.emit(False)
        self.signals.ui_list_enabled_changed.emit(False)
        self.signals.device_connecting.emit()

    def on_monitor_error(self, error):
        if not self.user_disconnecting and self.core.auto_reconnect_enabled:
            print(f"[AutoReconnect] 设备断开，尝试自动重连...")
            self._schedule_reconnect()
        else:
            self.disconnect_device()

    def update_heart_rate(self, heart_rate):
        if not self._first_heart_rate_received and heart_rate > 0:
            self._first_heart_rate_received = True
            if self.core.selected_device:
                self.settings_manager.increment_connection_count(self.core.selected_device.address)

        self.data_manager.collect_data(heart_rate)
        self.memory_share.update_heart_rate(heart_rate)

        self.signals.heart_rate_updated.emit(heart_rate)

    def update_status(self, status):
        print(f"[Status] {status}")
        self.signals.connection_status_changed.emit(status)

        if "设备连接成功" in status:
            self.core.reconnect_attempts = 0
            if self.core.selected_device:
                display_name = self._get_stable_device_name(self.core.selected_device.address, self.core.selected_device.name)
                display_text = self._get_device_display_text(self.core.selected_device.address, display_name)
                self.signals.device_connected.emit(display_text)

        elif "设备已断开连接" in status or "已断开连接" in status:
            self.signals.device_disconnected.emit()

    def disconnect_device(self):
        print(f"[DEBUG] disconnect_device called, is_disconnecting: {self.is_disconnecting}, user_disconnecting: {self.user_disconnecting}")

        if self.is_disconnecting:
            print("[DEBUG] Already disconnecting, skipping")
            return

        if not self.core.monitor_thread and not self.user_disconnecting:
            print("[DEBUG] Already disconnected, skipping")
            return

        self.is_disconnecting = True
        was_user_disconnecting = self.user_disconnecting
        self.user_disconnecting = True

        if self.core.monitor_thread:
            self.core.monitor_thread.stop()
            self.core.monitor_thread.join(timeout=3)
            self.core.monitor_thread = None

        self._cancel_reconnect_timer()

        self.signals.ui_connect_state_changed.emit(True, False)
        self.signals.ui_scan_state_changed.emit(True, "重新扫描")
        self.signals.ui_checkbox_enabled_changed.emit(True)
        self.signals.ui_list_enabled_changed.emit(True)
        self.update_status("已断开连接")

        self.user_disconnecting = False
        self.is_disconnecting = False
        self.core.reconnect_attempts = 0

        if not was_user_disconnecting:
            print(f"[DeviceManager] 设备意外断开，自动恢复扫描")
            threading.Timer(
                0.3,
                lambda: self.start_scan(self.settings_manager.get("filter_heart_rate_devices", True))
            ).start()

    def _schedule_reconnect(self):
        if self.core.reconnect_attempts >= self.core.max_reconnect_attempts:
            print(f"[AutoReconnect] 已达到最大重连次数 {self.core.max_reconnect_attempts}，放弃重连")
            self.disconnect_device()
            self.signals.info_bar_requested.emit("warn", "重连失败", f"已尝试 {self.core.max_reconnect_attempts} 次重连均失败，请手动重连")
            return

        self.core.reconnect_attempts += 1
        print(f"[AutoReconnect] 第 {self.core.reconnect_attempts}/{self.core.max_reconnect_attempts} 次重连，等待 {self.core.reconnect_interval} 秒...")

        if self.core.reconnect_attempts > 3:
            self.signals.info_bar_requested.emit("info", "正在重连", f"第 {self.core.reconnect_attempts}/{self.core.max_reconnect_attempts} 次重连...")

        self._cancel_reconnect_timer()
        self.reconnect_timer = threading.Timer(self.core.reconnect_interval, self._attempt_reconnect)
        self.reconnect_timer.daemon = True
        self.reconnect_timer.start()

    def _attempt_reconnect(self):
        self.reconnect_timer = None
        print(f"[AutoReconnect] 执行重连...")

        if self.core.monitor_thread:
            self.core.monitor_thread.stop()
            self.core.monitor_thread.join(timeout=3)
            self.core.monitor_thread = None

        if not self.core.selected_device:
            print("[AutoReconnect] 没有选中的设备，无法重连")
            self.disconnect_device()
            return

        selected_text = self._get_device_display_text(
            self.core.selected_device.address,
            self.core.selected_device.name
        )
        self.connect_device(selected_text)
