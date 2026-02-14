import asyncio
from PyQt6.QtCore import QThread, pyqtSignal
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

# 最大连接超时时间
timeout = 10

# 设备扫描线程
class DeviceScanThread(QThread):
    scan_finished = pyqtSignal(list)
    scan_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.filter_heart_rate_devices = False
    
    def run(self):
        try:
            devices = asyncio.run(self.scan_devices())
            self.scan_finished.emit(devices)
        except Exception as e:
            self.scan_error.emit(str(e))
    
    async def scan_devices(self):
        devices = await BleakScanner.discover()
        
        # 如果需要筛选心率设备
        if self.filter_heart_rate_devices:
            filtered_devices = []
            for device in devices:
                try:
                    # 尝试连接设备并检查是否有心率服务
                    async with BleakClient(device) as client:
                        has_heart_rate_service = False
                        for service in client.services:
                            # 检查服务UUID是否包含心率服务的特征
                            # 心率服务UUID通常是 '180d'
                            if '180d' in service.uuid.lower():
                                has_heart_rate_service = True
                                break
                        if has_heart_rate_service:
                            filtered_devices.append(device)
                except:
                    # 连接失败的设备跳过
                    pass
            return filtered_devices
        
        return devices

# 心率监测线程
class HeartRateMonitorThread(QThread):
    heart_rate_updated = pyqtSignal(int)
    connection_status = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, device):
        super().__init__()
        self.device = device
        self.running = False
        self.client = None
    
    def run(self):
        try:
            self.running = True
            asyncio.run(self.monitor_heart_rate())
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        self.running = False
        # 移除嵌套的asyncio.run调用，只设置running为False
        # 线程中的while循环会自动退出，然后在monitor_heart_rate方法中正常断开连接
    
    async def monitor_heart_rate(self):
        def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
            try:
                value = int(data.hex().split('06')[1], 16)
                self.heart_rate_updated.emit(value)
            except Exception as e:
                self.error_occurred.emit(f"解析心率数据出错: {e}")
        
        try:
            self.connection_status.emit("正在连接设备...")
            
            def disconnected_callback(client):
                self.connection_status.emit("设备已断开连接")
                self.running = False
            
            async with BleakClient(self.device, disconnected_callback=disconnected_callback, timeout=timeout) as client:
                self.client = client
                self.connection_status.emit("设备连接成功")
                
                self.connection_status.emit("正在查找心率测量特征...")
                hr_measurement_uuid = None
                for service in client.services:
                    for characteristic in service.characteristics:
                        if "Heart Rate Measurement" in characteristic.description:
                            hr_measurement_uuid = characteristic.uuid
                            break
                    if hr_measurement_uuid:
                        break
                
                if hr_measurement_uuid:
                    self.connection_status.emit("开始心率监测")
                    await client.start_notify(hr_measurement_uuid, notification_handler)
                    
                    while self.running:
                        await asyncio.sleep(0.1)
                    
                    await client.stop_notify(hr_measurement_uuid)
                else:
                    self.error_occurred.emit("未找到心率测量特征")
        except Exception as e:
            self.error_occurred.emit(f"连接失败: {e}")

# 心率监测器核心类
class HeartRateMonitorCore:
    """
    心率监测器的核心功能类，处理设备连接和数据监控逻辑
    """
    def __init__(self):
        self.devices = []
        self.selected_device = None
        self.monitor_thread = None
        self.scan_thread = None
    
    def is_device_supported(self, device):
        """
        检查设备是否支持心率监测
        实际使用时可以根据设备名称或其他特征进行判断
        """
        # 这里简化处理，实际可能需要更复杂的判断逻辑
        return True
    
    def cleanup(self):
        """
        清理资源，停止所有线程
        """
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.wait()