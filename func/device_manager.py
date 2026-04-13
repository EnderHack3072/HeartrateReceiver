from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from qfluentwidgets import InfoBar, InfoBarPosition
from func.core import HeartRateMonitorCore, DeviceScanThread, HeartRateMonitorThread, DeviceInfo


class DeviceManager:
    def __init__(self, window):
        self.window = window
        self.settings_manager = window.settings_manager
        self.core = HeartRateMonitorCore(window.settings_manager)
        self.user_disconnecting = False
        self.is_disconnecting = False
        self.data_manager = window.data_manager
        self.memory_share = window.memory_share
        
        self.discovered_devices = {}
        self.MAX_DEVICES = 100
        
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self._attempt_reconnect)
    
    def start_scan(self):
        self.discovered_devices.clear()
        self.core.devices = []
        self.window.homePage.listWidget.clear()
        
        self.window.homePage.scanButton.setEnabled(False)
        self.window.homePage.scanButton.setText("扫描中...")
        self.window.homePage.progressBar.setCustomBarColor(QColor(0, 159, 170), QColor(0, 130, 140))
        self.window.homePage.progressBar.hide()
        self.window.homePage.indeterminateBar.show()
        self.window.homePage.indeterminateBar.start()
        
        self.core.scan_thread = DeviceScanThread()
        self.core.scan_thread.filter_heart_rate_devices = self.window.homePage.checkBox.isChecked()
        self.core.scan_thread.scan_started.connect(self._on_scan_started)
        self.core.scan_thread.scan_finished.connect(self.on_scan_finished)
        self.core.scan_thread.scan_error.connect(self.on_scan_error)
        self.core.scan_thread.device_found.connect(self._on_device_found)
        self.core.scan_thread.device_updated.connect(self._on_device_updated)
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
        
        device_name = self._get_stable_device_name(address, device_info.name)
        display_text = self._get_device_display_text(address, device_name)
        
        # 使用QTimer确保在主线程中执行UI操作
        QTimer.singleShot(0, lambda: self._add_device_to_list(display_text))
        
        print(f"[DeviceManager] 添加设备到列表: {display_text}")
    
    def _add_device_to_list(self, display_text):
        """在主线程中添加设备到列表并排序"""
        try:
            self.window.homePage.listWidget.addItem(display_text)
            self._sort_device_list()
            self.window.homePage.connectButton.setEnabled(True)
        except Exception as e:
            print(f"[DeviceManager] 添加设备到列表时出错: {e}")
    
    def _on_device_updated(self, device_info):
        address = device_info.address
        
        if address not in self.discovered_devices:
            return
        
        self.discovered_devices[address] = device_info
        
        new_device_name = self._get_stable_device_name(address, device_info.name)
        current_display_text = self._get_device_display_text(address, new_device_name)
        
        # 使用QTimer确保在主线程中执行UI操作
        QTimer.singleShot(0, lambda: self._update_device_display(address, current_display_text))
    
    def _update_device_display(self, address, current_display_text):
        """在主线程中更新设备显示并排序"""
        try:
            for i in range(self.window.homePage.listWidget.count()):
                item_text = self.window.homePage.listWidget.item(i).text()
                if address in item_text or item_text == current_display_text:
                    if item_text != current_display_text:
                        self.window.homePage.listWidget.item(i).setText(current_display_text)
                        print(f"[DeviceManager] 更新设备显示: {address} -> {current_display_text}")
                        self._sort_device_list()
                    break
        except Exception as e:
            print(f"[DeviceManager] 更新设备显示时出错: {e}")
    
    def _sort_device_list(self):
        """对设备列表进行排序：有设备名的在前，只有MAC地址的在后"""
        # 直接在主线程中执行排序操作
        try:
            # 检查listWidget是否存在
            if not hasattr(self.window, 'homePage') or not hasattr(self.window.homePage, 'listWidget'):
                return
            
            # 获取所有设备项
            items = []
            count = self.window.homePage.listWidget.count()
            
            for i in range(count):
                item = self.window.homePage.listWidget.item(i)
                if item:
                    try:
                        text = item.text()
                        items.append((text, item))
                    except Exception:
                        pass
            
            # 排序规则：有设备名的在前，只有MAC地址的在后
            def sort_key(item_tuple):
                try:
                    text, item = item_tuple
                    # 检查是否是MAC地址（通常是由冒号分隔的12个十六进制字符）
                    is_mac_only = ':' in text and len(text) == 17
                    return (is_mac_only, text)
                except Exception:
                    return (True, "")
            
            # 排序
            sorted_items = sorted(items, key=sort_key)
            
            # 清空列表
            self.window.homePage.listWidget.clear()
            
            # 重新添加到列表
            for text, item in sorted_items:
                try:
                    self.window.homePage.listWidget.addItem(text)
                except Exception:
                    pass
        except Exception:
            pass
    
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
            self.window.homePage.connectButton.setEnabled(False)
            InfoBar.warning(
                title="未发现设备",
                content="没有扫描到任何设备",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window
            )
            self._finish_scan_ui(success=False)
    
    def _finish_scan_ui(self, success):
        self.window.homePage.indeterminateBar.stop()
        self.window.homePage.indeterminateBar.hide()
        self.window.homePage.progressBar.setValue(100)
        
        if not success:
            self.window.homePage.progressBar.setCustomBarColor(QColor(196, 43, 28), QColor(160, 30, 15))
        
        self.window.homePage.progressBar.show()
        self.window.homePage.scanButton.setEnabled(True)
        self.window.homePage.scanButton.setText("重新扫描")
    
    def on_scan_error(self, error):
        self.window.homePage.indeterminateBar.stop()
        self.window.homePage.indeterminateBar.hide()
        self.window.homePage.progressBar.setValue(100)
        self.window.homePage.progressBar.setCustomBarColor(QColor(196, 43, 28), QColor(160, 30, 15))
        self.window.homePage.progressBar.show()
        self.window.homePage.scanButton.setEnabled(True)
        self.window.homePage.scanButton.setText("重新扫描")
        
        InfoBar.error(
            title="扫描出错：",
            content=f"{error}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self.window
        )
    
    def stop_scan(self):
        if self.core.scan_thread and self.core.scan_thread.isRunning():
            self.core.scan_thread.stop()
            self.core.scan_thread.wait()
            self.core.scan_thread = None
            
            self.window.homePage.indeterminateBar.stop()
            self.window.homePage.indeterminateBar.hide()
            self.window.homePage.progressBar.setValue(100)
            self.window.homePage.progressBar.show()
    
    def connect_device(self):
        if self.window.homePage.listWidget.currentRow() == -1:
            InfoBar.warning(
                title="请选择设备",
                content="请先选择要连接的设备",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window
            )
            return
        
        index = self.window.homePage.listWidget.currentRow()
        selected_text = self.window.homePage.listWidget.item(index).text()
        
        selected_info = None
        device_list = list(self.discovered_devices.values())
        
        for info in device_list:
            display_name = self._get_stable_device_name(info.address, info.name)
            display_text = self._get_device_display_text(info.address, display_name)
            if display_text == selected_text:
                selected_info = info
                break
        
        if not selected_info:
            InfoBar.warning(
                title="设备选择错误",
                content="请重新选择设备",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window
            )
            return
        
        self.core.selected_device = selected_info.device
        self.core.devices = device_list
        
        if not self.core.is_device_supported(self.core.selected_device):
            InfoBar.warning(
                title="设备不支持",
                content="请重新选择",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window
            )
            return
        
        self.stop_scan()
        
        if self.core.monitor_thread:
            self.core.monitor_thread.stop()
            self.core.monitor_thread.wait()
            self.core.monitor_thread = None
        
        self.core.monitor_thread = HeartRateMonitorThread(self.core.selected_device)
        self.core.monitor_thread.heart_rate_updated.connect(self.update_heart_rate)
        self.core.monitor_thread.connection_status.connect(self.update_status)
        self.core.monitor_thread.error_occurred.connect(self.on_monitor_error)
        self.core.monitor_thread.start()
        
        self.window.homePage.connectButton.setEnabled(False)
        self.window.homePage.disconnectButton.setEnabled(True)
        self.window.homePage.scanButton.setEnabled(False)
        self.window.homePage.checkBox.setEnabled(False)
        self.window.homePage.listWidget.setEnabled(False)
    
    def on_monitor_error(self, error):
        if not self.user_disconnecting and self.core.auto_reconnect_enabled:
            print(f"[AutoReconnect] 设备断开，尝试自动重连...")
            self._schedule_reconnect()
        else:
            self.disconnect_device()
    
    def update_heart_rate(self, heart_rate):
        self.data_manager.collect_data(heart_rate)
        self.memory_share.update_heart_rate(heart_rate)
        
        if hasattr(self.window, 'homePage') and hasattr(self.window.homePage, 'lineChartPage') and hasattr(self.window.homePage.lineChartPage, 'chart'):
            chart = self.window.homePage.lineChartPage.chart
            chart.add_value(heart_rate)
            
            if hasattr(self.window.homePage.lineChartPage, 'top_right_label') and hasattr(self.window.homePage.lineChartPage, 'bottom_right_label'):
                if hasattr(chart, 'MAX_Y') and hasattr(chart, 'MIN_Y'):
                    self.window.homePage.lineChartPage.top_right_label.setText(f"{chart.MAX_Y}")
                    self.window.homePage.lineChartPage.bottom_right_label.setText(f"{chart.MIN_Y}")
                else:
                    self.window.homePage.lineChartPage.top_right_label.setText("200")
                    self.window.homePage.lineChartPage.bottom_right_label.setText("0")
        
        if hasattr(self.window, 'homePage') and hasattr(self.window.homePage, 'trendChartPage'):
            self.window.homePage.trendChartPage.update_heart_rate(heart_rate)
    
    def update_status(self, status):
        print(f"[Status] {status}")
        
        if "设备连接成功" in status:
            self.core.reconnect_attempts = 0
            if hasattr(self.window, 'homePage') and hasattr(self.window.homePage, 'lineChartPage') and hasattr(self.window.homePage.lineChartPage, 'chart'):
                self.window.homePage.lineChartPage.chart.set_receiving_state(True)
        
        elif "设备已断开连接" in status or "已断开连接" in status:
            if hasattr(self.window, 'homePage') and hasattr(self.window.homePage, 'lineChartPage') and hasattr(self.window.homePage.lineChartPage, 'chart'):
                self.window.homePage.lineChartPage.chart.set_receiving_state(False)
        
        if hasattr(self.window, 'homePage') and hasattr(self.window.homePage, 'lineChartPage'):
            line_chart_page = self.window.homePage.lineChartPage
            if hasattr(line_chart_page, 'right_label'):
                if "设备连接成功" in status:
                    if hasattr(self.core, 'selected_device') and self.core.selected_device:
                        address = self.core.selected_device.address
                        device_name = self.settings_manager.get_device_name(address)
                        display_text = self._get_device_display_text(address, device_name)
                        line_chart_page.right_label.setText(display_text)
                elif "设备已断开连接" in status or "请先连接设备" in status:
                    line_chart_page.right_label.setText("请先连接设备")
    
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
            self.core.monitor_thread.wait()
            self.core.monitor_thread = None
        
        self.window.homePage.connectButton.setEnabled(True)
        self.window.homePage.disconnectButton.setEnabled(False)
        self.window.homePage.scanButton.setEnabled(True)
        self.window.homePage.checkBox.setEnabled(True)
        self.window.homePage.listWidget.setEnabled(True)
        self.update_status("已断开连接")
        self.update_heart_rate(0)
        
        self.user_disconnecting = False
        self.is_disconnecting = False
        self.core.reconnect_attempts = 0
        self.reconnect_timer.stop()
        
        if not was_user_disconnecting:
            print(f"[DeviceManager] 设备意外断开，自动恢复扫描")
            QTimer.singleShot(300, self.start_scan)
    
    def _schedule_reconnect(self):
        if self.core.reconnect_attempts >= self.core.max_reconnect_attempts:
            print(f"[AutoReconnect] 已达到最大重连次数 {self.core.max_reconnect_attempts}，放弃重连")
            self.disconnect_device()
            InfoBar.warning(
                title="重连失败",
                content=f"已尝试 {self.core.max_reconnect_attempts} 次重连均失败，请手动重连",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self.window
            )
            return
        
        wait_time = self.core.reconnect_interval * 1000
        self.core.reconnect_attempts += 1
        print(f"[AutoReconnect] 第 {self.core.reconnect_attempts}/{self.core.max_reconnect_attempts} 次重连，等待 {self.core.reconnect_interval} 秒...")
        
        if self.core.reconnect_attempts > 3:
            InfoBar.info(
                title="正在重连",
                content=f"第 {self.core.reconnect_attempts}/{self.core.max_reconnect_attempts} 次重连...",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window
            )
        
        self.reconnect_timer.start(wait_time)
    
    def _attempt_reconnect(self):
        print(f"[AutoReconnect] 执行重连...")
        
        if self.core.monitor_thread:
            self.core.monitor_thread.stop()
            self.core.monitor_thread.wait()
            self.core.monitor_thread = None
        
        if not self.core.selected_device:
            print("[AutoReconnect] 没有选中的设备，无法重连")
            self.disconnect_device()
            return
        
        self.connect_device()
