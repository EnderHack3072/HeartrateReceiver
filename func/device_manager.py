from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from qfluentwidgets import InfoBar, InfoBarPosition
from func.core import HeartRateMonitorCore, DeviceScanThread, HeartRateMonitorThread, DeviceInfo, HeartRateSimulatorThread


class DeviceManager:
    """设备管理器，负责设备扫描和连接"""
    
    def __init__(self, window):
        self.window = window
        self.settings_manager = window.settings_manager
        self.core = HeartRateMonitorCore(window.settings_manager)
        self.user_disconnecting = False
        self.is_disconnecting = False
        self.data_manager = window.data_manager
        self.memory_share = window.memory_share
        self.simulator_mode = False
        self.simulator_device_address = "SIMULATOR-DEVICE-001"
        self.simulator_activated = False  # 只有用户主动激活后才会显示模拟设备
        
        # 设备存储
        self.discovered_devices = {}
        self.MAX_DEVICES = 100
        
        # 重连定时器
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self._attempt_reconnect)
    
    def start_scan(self):
        """开始扫描设备"""
        # 清除设备列表，但保留稳定名称缓存
        self.discovered_devices.clear()
        self.core.devices = []
        self.window.homePage.listWidget.clear()
        
        # 只有用户主动激活后才添加模拟设备
        if self.simulator_activated:
            self._add_simulator_device()
        
        # 更新UI状态
        self.window.homePage.scanButton.setEnabled(False)
        self.window.homePage.scanButton.setText("扫描中...")
        self.window.homePage.progressBar.setCustomBarColor(QColor(0, 159, 170), QColor(0, 130, 140))
        self.window.homePage.progressBar.hide()
        self.window.homePage.indeterminateBar.show()
        self.window.homePage.indeterminateBar.start()
        
        # InfoBar.info(
        #     title="正在扫描设备...",
        #     content="扫描周期为30秒，发现设备将实时显示",
        #     orient=Qt.Orientation.Horizontal,
        #     isClosable=True,
        #     position=InfoBarPosition.TOP,
        #     duration=3000,
        #     parent=self.window
        # )
        
        # 创建并启动扫描线程
        self.core.scan_thread = DeviceScanThread()
        self.core.scan_thread.filter_heart_rate_devices = self.window.homePage.checkBox.isChecked()
        self.core.scan_thread.scan_started.connect(self._on_scan_started)
        self.core.scan_thread.scan_finished.connect(self.on_scan_finished)
        self.core.scan_thread.scan_error.connect(self.on_scan_error)
        self.core.scan_thread.device_found.connect(self._on_device_found)
        self.core.scan_thread.device_updated.connect(self._on_device_updated)
        self.core.scan_thread.start()
    
    def _add_simulator_device(self):
        """添加模拟设备到设备列表"""
        class DummyDevice:
            def __init__(self, address, name):
                self.address = address
                self.name = name
        
        dummy_device = DummyDevice(self.simulator_device_address, "模拟心率设备 (Debug)")
        device_info = DeviceInfo(dummy_device, None)
        device_info.name = "模拟心率设备 (Debug)"
        
        self.discovered_devices[self.simulator_device_address] = device_info
        self.window.homePage.listWidget.addItem("模拟心率设备 (Debug)")
        self.window.homePage.connectButton.setEnabled(True)
        
        print(f"[DeviceManager] 添加模拟设备到列表: 模拟心率设备 (Debug)")
    
    def _on_scan_started(self):
        """扫描开始回调"""
        print("[DeviceManager] 扫描已开始")
    
    def _get_device_display_text(self, address, name):
        """获取设备显示文本
        
        Args:
            address: 设备MAC地址
            name: 设备名称（可能为None）
        
        Returns:
            str: 显示文本 - 有名称时只显示名称，无名称时只显示MAC地址
        """
        if name and name.strip():
            return name
        else:
            return address
    
    def _on_device_found(self, device_info):
        """发现新设备"""
        address = device_info.address
        
        if address in self.discovered_devices:
            return
        
        if len(self.discovered_devices) >= self.MAX_DEVICES:
            print(f"[DeviceManager] 已达到最大设备数量限制 {self.MAX_DEVICES}")
            return
        
        self.discovered_devices[address] = device_info
        
        # 获取稳定的设备名称
        device_name = self._get_stable_device_name(address, device_info.name)
        
        # 生成显示文本
        display_text = self._get_device_display_text(address, device_name)
        
        # 添加到UI
        self.window.homePage.listWidget.addItem(display_text)
        self.window.homePage.connectButton.setEnabled(True)
        
        print(f"[DeviceManager] 添加设备到列表: {display_text}")
    
    def _on_device_updated(self, device_info):
        """设备信息更新"""
        address = device_info.address
        
        if address not in self.discovered_devices:
            return
        
        self.discovered_devices[address] = device_info
        
        # 更新稳定名称
        new_device_name = self._get_stable_device_name(address, device_info.name)
        
        # 更新UI中的显示
        current_display_text = self._get_device_display_text(address, new_device_name)
        
        for i in range(self.window.homePage.listWidget.count()):
            item_text = self.window.homePage.listWidget.item(i).text()
            # 检查是否匹配（通过地址检查或显示文本检查）
            if address in item_text or item_text == current_display_text:
                if item_text != current_display_text:
                    self.window.homePage.listWidget.item(i).setText(current_display_text)
                    print(f"[DeviceManager] 更新设备显示: {address} -> {current_display_text}")
                break
    
    def _get_stable_device_name(self, address, current_name):
        """获取稳定的设备名称（持久化存储）
        
        Args:
            address: 设备MAC地址
            current_name: 当前扫描到的设备名称
        
        Returns:
            str: 稳定的设备名称，如果没有有效名称返回None
        """
        valid_name = current_name if current_name and current_name.strip() and current_name != "未知设备" else None
        
        # 从持久化存储中获取缓存名称
        cached_name = self.settings_manager.get_device_name(address)
        
        if cached_name:
            # 如果有缓存的有效名称
            if valid_name and valid_name != cached_name:
                # 如果有新的有效名称，更新持久化存储
                print(f"[DeviceManager] 更新稳定名称: {address}: {cached_name} -> {valid_name}")
                self.settings_manager.set_device_name(address, valid_name)
                return valid_name
            return cached_name
        else:
            # 没有缓存的名称
            if valid_name:
                self.settings_manager.set_device_name(address, valid_name)
                return valid_name
            # 没有有效名称时返回None，不保存"未知设备"
            return None
    
    def on_scan_finished(self, devices):
        """扫描完成"""
        self.core.devices = devices
        
        if self.discovered_devices:
            # InfoBar.success(
            #     title="扫描完成",
            #     content=f"发现 {len(self.discovered_devices)} 个设备",
            #     orient=Qt.Orientation.Horizontal,
            #     isClosable=True,
            #     position=InfoBarPosition.TOP,
            #     duration=3000,
            #     parent=self.window
            # )
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
        """完成扫描的UI更新"""
        self.window.homePage.indeterminateBar.stop()
        self.window.homePage.indeterminateBar.hide()
        self.window.homePage.progressBar.setValue(100)
        
        if not success:
            self.window.homePage.progressBar.setCustomBarColor(QColor(196, 43, 28), QColor(160, 30, 15))
        
        self.window.homePage.progressBar.show()
        self.window.homePage.scanButton.setEnabled(True)
        self.window.homePage.scanButton.setText("重新扫描")
    
    def on_scan_error(self, error):
        """扫描出错"""
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
        """停止正在进行的扫描"""
        if self.core.scan_thread and self.core.scan_thread.isRunning():
            self.core.scan_thread.stop()
            self.core.scan_thread.wait()
            self.core.scan_thread = None
            
            self.window.homePage.indeterminateBar.stop()
            self.window.homePage.indeterminateBar.hide()
            self.window.homePage.progressBar.setValue(100)
            self.window.homePage.progressBar.show()
            
            # InfoBar.info(
            #     title="已停止扫描",
            #     content="扫描进程已停止",
            #     orient=Qt.Orientation.Horizontal,
            #     isClosable=True,
            #     position=InfoBarPosition.TOP,
            #     duration=2000,
            #     parent=self.window
            # )
    
    def connect_device(self):
        """连接设备"""
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
        
        # 检查是否是模拟设备
        if selected_text == "模拟心率设备 (Debug)":
            self.start_simulator()
            return
        
        # 通过显示文本找到对应的设备（因为现在可能只显示名称或只显示地址）
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
        """监测错误"""
        if not self.user_disconnecting:
            if not self.core.auto_reconnect_enabled:
                # InfoBar.info(
                #     title="设备已断开连接，正在重新扫描...",
                #     content="设备连接已断开，将自动重新扫描设备",
                #     orient=Qt.Orientation.Horizontal,
                #     isClosable=True,
                #     position=InfoBarPosition.TOP,
                #     duration=4000,
                #     parent=self.window
                # )
                pass
        
        if not self.user_disconnecting and self.core.auto_reconnect_enabled:
            print(f"[AutoReconnect] 设备断开，尝试自动重连...")
            self._schedule_reconnect()
        else:
            self.disconnect_device()
    
    def update_heart_rate(self, heart_rate):
        """更新心率数值"""
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
        """更新状态信息"""
        print(f"[Status] {status}")
        
        if "设备连接成功" in status:
            self.core.reconnect_attempts = 0
            # print(f"[AutoReconnect] 连接成功，重置重连次数")
            # InfoBar.success(
            #     title="设备连接成功",
            #     content="设备已成功连接，开始心率监测",
            #     orient=Qt.Orientation.Horizontal,
            #     isClosable=True,
            #     position=InfoBarPosition.TOP,
            #     duration=3000,
            #     parent=self.window
            # )
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
                        # 使用统一的设备显示逻辑
                        device_name = self.settings_manager.get_device_name(address)
                        display_text = self._get_device_display_text(address, device_name)
                        line_chart_page.right_label.setText(display_text)
                elif "设备已断开连接" in status or "请先连接设备" in status:
                    line_chart_page.right_label.setText("请先连接设备")
    
    def disconnect_device(self):
        """断开设备"""
        print(f"[DEBUG] disconnect_device called, is_disconnecting: {self.is_disconnecting}, user_disconnecting: {self.user_disconnecting}")
        
        if self.is_disconnecting:
            print("[DEBUG] Already disconnecting, skipping")
            return
        
        # 如果是模拟模式，直接调用停止模拟方法
        if self.simulator_mode:
            self.stop_simulator()
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
        """安排重连"""
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
        """执行重连"""
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
    
    def toggle_simulator_mode(self):
        """切换模拟模式"""
        if self.simulator_mode:
            # 关闭模拟模式
            self.stop_simulator()
        else:
            # 开启模拟模式
            self.start_simulator()
    
    def start_simulator(self):
        """启动心率模拟"""
        print("[Simulator] 启动心率模拟...")
        
        # 断开当前连接（但避免递归调用）
        if self.core.monitor_thread and not self.simulator_mode:
            self.is_disconnecting = True
            if self.core.monitor_thread:
                self.core.monitor_thread.stop()
                self.core.monitor_thread.wait()
                self.core.monitor_thread = None
            self.is_disconnecting = False
        
        self.simulator_mode = True
        self.core.simulator_mode = True
        self.data_manager.simulator_mode = True
        
        # 启动模拟线程
        self.core.monitor_thread = HeartRateSimulatorThread()
        self.core.monitor_thread.heart_rate_updated.connect(self.update_heart_rate)
        self.core.monitor_thread.connection_status.connect(self.update_status)
        self.core.monitor_thread.error_occurred.connect(self.on_monitor_error)
        self.core.monitor_thread.start()
        
        # 更新UI状态
        self.window.homePage.scanButton.setEnabled(False)
        self.window.homePage.connectButton.setEnabled(False)
        self.window.homePage.disconnectButton.setEnabled(True)
        self.window.homePage.checkBox.setEnabled(False)
        self.window.homePage.listWidget.setEnabled(False)
        
        InfoBar.success(
            title="模拟模式已启用",
            content="心率数据模拟已开始（60-120次/分钟）",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window
        )
    
    def stop_simulator(self):
        """停止心率模拟"""
        print("[Simulator] 停止心率模拟...")
        
        if self.core.monitor_thread:
            self.core.monitor_thread.stop()
            self.core.monitor_thread.wait()
            self.core.monitor_thread = None
        
        self.simulator_mode = False
        self.core.simulator_mode = False
        self.data_manager.simulator_mode = False
        
        # 更新状态信息
        self.update_status("已断开连接")
        
        # 重置UI状态
        self.window.homePage.scanButton.setEnabled(True)
        self.window.homePage.disconnectButton.setEnabled(False)
        self.window.homePage.checkBox.setEnabled(True)
        self.window.homePage.listWidget.setEnabled(True)
        
        # 如果设备列表中还有模拟设备，启用连接按钮
        list_widget = self.window.homePage.listWidget
        has_simulator = False
        for i in range(list_widget.count()):
            if list_widget.item(i).text() == "模拟心率设备 (Debug)":
                has_simulator = True
                if list_widget.currentRow() == i:
                    self.window.homePage.connectButton.setEnabled(True)
                break
        
        if not has_simulator and self.simulator_activated:
            # 如果已激活但列表中没有，重新添加
            self._add_simulator_device()
        
        # 更新数据为0
        self.update_heart_rate(0)
        
        # 重置与重连相关的状态
        self.core.reconnect_attempts = 0
        self.reconnect_timer.stop()
        
        InfoBar.info(
            title="模拟模式已关闭",
            content="心率数据模拟已停止",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self.window
        )
