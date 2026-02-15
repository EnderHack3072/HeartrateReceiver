from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from qfluentwidgets import InfoBar, InfoBarPosition
from func.core import HeartRateMonitorCore, DeviceScanThread, HeartRateMonitorThread

class DeviceManager:
    """设备管理器，负责设备扫描和连接"""
    def __init__(self, window):
        self.window = window
        self.core = HeartRateMonitorCore(window.settings_manager)
        self.user_disconnecting = False  # 标记用户是否正在主动断开连接
        self.is_disconnecting = False  # 标记是否正在执行断开连接操作，防止重复调用
        self.data_manager = window.data_manager
        self.memory_share = window.memory_share
        
        # 重连定时器
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self._attempt_reconnect)
    
    # 扫描设备
    def start_scan(self):
        self.window.homePage.scanButton.setEnabled(False)
        self.window.homePage.scanButton.setText("扫描中...")
        # 设置静止进度条颜色为 #009FAA
        self.window.homePage.progressBar.setCustomBarColor(QColor(0, 159, 170), QColor(0, 130, 140))
        # 显示不确定进度条，隐藏普通进度条
        self.window.homePage.progressBar.hide()
        self.window.homePage.indeterminateBar.show()
        self.window.homePage.indeterminateBar.start()
        self.core.scan_thread = DeviceScanThread()
        # 传递自动筛选状态给扫描线程
        self.core.scan_thread.filter_heart_rate_devices = self.window.homePage.checkBox.isChecked()
        self.core.scan_thread.scan_finished.connect(self.on_scan_finished)
        self.core.scan_thread.scan_error.connect(self.on_scan_error)
        self.core.scan_thread.start()

    def on_scan_finished(self, devices):
        self.core.devices = devices
        self.window.homePage.listWidget.clear()

        if devices:
            for device in devices:
                device_name = device.name if device.name else "未知设备"
                self.window.homePage.listWidget.addItem(f"{device_name} ({device.address})") 
            self.window.homePage.connectButton.setEnabled(True)
            InfoBar.success(
                title="扫描完成",
                content=f"发现 {len(devices)} 个设备",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window
            )
            # 扫描完成且找到设备，显示普通进度条（100%），隐藏不确定进度条
            self.window.homePage.indeterminateBar.stop()
            self.window.homePage.indeterminateBar.hide()
            self.window.homePage.progressBar.setValue(100)
            # 重置进度条颜色为默认颜色
            self.window.homePage.progressBar.show()
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
            # 扫描完成但未发现设备，显示暗红色普通进度条，隐藏不确定进度条
            self.window.homePage.indeterminateBar.stop()
            self.window.homePage.indeterminateBar.hide()
            self.window.homePage.progressBar.setValue(100)
            # 设置错误状态颜色为暗红色 C42B1C
            self.window.homePage.progressBar.setCustomBarColor(QColor(196, 43, 28), QColor(160, 30, 15))
            self.window.homePage.progressBar.show()

        self.window.homePage.scanButton.setEnabled(True)
        self.window.homePage.scanButton.setText("重新扫描")

    def on_scan_error(self, error):
        # 扫描出错，显示暗红色普通进度条，隐藏不确定进度条
        self.window.homePage.indeterminateBar.stop()
        self.window.homePage.indeterminateBar.hide()
        self.window.homePage.progressBar.setValue(100)
        # 设置错误状态颜色为暗红色 C42B1C
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

    # 连接设备
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
        self.core.selected_device = self.core.devices[index]

        # 检查设备是否支持
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

        # 确保之前的线程已经停止
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
        # 禁用勾选框和列表框
        self.window.homePage.checkBox.setEnabled(False)
        self.window.homePage.listWidget.setEnabled(False)

    def on_monitor_error(self, error):
        # 如果是用户主动断开连接，不显示提示
        # 如果启用了自动重连，也不显示设备断开提示
        if not self.user_disconnecting and not self.core.auto_reconnect_enabled:
            InfoBar.info(
                title="设备已断开",
                content="设备连接已断开，您可以重新扫描或连接其他设备",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self.window
            )
        
        # 尝试自动重连（如果启用且不是用户主动断开）
        if not self.user_disconnecting and self.core.auto_reconnect_enabled:
            print(f"[AutoReconnect] 设备断开，尝试自动重连...")
            self._schedule_reconnect()
        else:
            self.disconnect_device()

    # 更新心率数值
    def update_heart_rate(self, heart_rate):
        """处理心率数据"""
        # 这里可以添加心率数据的处理逻辑
        # 例如：存储心率数据、更新共享内存、进行异常检测等
        #print(f"[Heart Rate] 心率: {heart_rate}")
        
        self.data_manager.collect_data(heart_rate)
        self.memory_share.update_heart_rate(heart_rate)
        
        # 将心率数据传递给右上卡片中的折线图
        if hasattr(self.window, 'homePage') and hasattr(self.window.homePage, 'lineChartPage') and hasattr(self.window.homePage.lineChartPage, 'chart'):
            chart = self.window.homePage.lineChartPage.chart
            chart.add_value(heart_rate)
            
            # 更新范围标签（显示折线图当前显示范围）
            if hasattr(self.window.homePage.lineChartPage, 'top_right_label') and hasattr(self.window.homePage.lineChartPage, 'bottom_right_label'):
                # 获取折线图当前显示范围
                if hasattr(chart, 'MAX_Y') and hasattr(chart, 'MIN_Y'):
                    # 更新范围标签，右上角显示最大值，右下角显示最小值
                    self.window.homePage.lineChartPage.top_right_label.setText(f"{chart.MAX_Y}")
                    self.window.homePage.lineChartPage.bottom_right_label.setText(f"{chart.MIN_Y}")
                else:
                    # 数据不足时显示默认范围
                    self.window.homePage.lineChartPage.top_right_label.setText("200")
                    self.window.homePage.lineChartPage.bottom_right_label.setText("0")
        
        # 将心率数据传递给右下卡片中的趋势折线图页面
        if hasattr(self.window, 'homePage') and hasattr(self.window.homePage, 'trendChartPage'):
            self.window.homePage.trendChartPage.update_heart_rate(heart_rate)

    # 更新状态信息
    def update_status(self, status):
        """处理状态信息"""
        # 这里可以添加状态信息的处理逻辑
        print(f"[Status] {status}")
        
        # 连接成功时重置重连尝试次数
        if "设备连接成功" in status:
            self.core.reconnect_attempts = 0
            print(f"[AutoReconnect] 连接成功，重置重连次数")
        
        # 更新右上卡片中的状态信息
        if hasattr(self.window, 'homePage') and hasattr(self.window.homePage, 'lineChartPage'):
            line_chart_page = self.window.homePage.lineChartPage
            # 更新右上角设备名称标签
            if hasattr(line_chart_page, 'right_label'):
                if "设备连接成功" in status:
                    if hasattr(self.core, 'selected_device') and self.core.selected_device:
                        device_name = self.core.selected_device.name if self.core.selected_device.name else "未知设备"
                        line_chart_page.right_label.setText(device_name)
                elif "设备已断开连接" in status or "请先连接设备" in status:
                    line_chart_page.right_label.setText("请先连接设备")
        
        # 更新右下卡片中的趋势图表页面状态信息
        # 已删除设备名称标签，无需更新

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

        self.window.homePage.connectButton.setEnabled(True)
        self.window.homePage.disconnectButton.setEnabled(False)
        self.window.homePage.scanButton.setEnabled(True)
        # 重新启用勾选框和列表框
        self.window.homePage.checkBox.setEnabled(True)
        self.window.homePage.listWidget.setEnabled(True)
        self.update_status("已断开连接")
        self.update_heart_rate(0)

        # 重置标志
        self.user_disconnecting = False
        self.is_disconnecting = False
        
        # 重置重连尝试次数
        self.core.reconnect_attempts = 0
        # 停止重连定时器
        self.reconnect_timer.stop()
    
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
        
        # 前3次重连不显示横幅
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
        
        # 先清理之前的连接
        if self.core.monitor_thread:
            self.core.monitor_thread.stop()
            self.core.monitor_thread.wait()
            self.core.monitor_thread = None
        
        # 检查是否还有选中的设备
        if not self.core.selected_device:
            print("[AutoReconnect] 没有选中的设备，无法重连")
            self.disconnect_device()
            return
        
        # 重连设备
        self.connect_device()
