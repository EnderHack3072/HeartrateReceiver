import asyncio
import random
import os
from PyQt6.QtCore import QThread, pyqtSignal
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

# 最大连接超时时间
timeout = 10

# 心率服务 UUID
HEART_RATE_SERVICE_UUID = "180d"


class DeviceInfo:
    """设备信息数据类，用于存储设备信息"""
    
    def __init__(self, device, advertisement_data=None):
        self.device = device
        self.address = device.address
        self.name = self._extract_name(device, advertisement_data)
        self.rssi = advertisement_data.rssi if advertisement_data and hasattr(advertisement_data, 'rssi') else None
        self.advertisement_data = advertisement_data
        self.last_seen = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
    
    def _extract_name(self, device, advertisement_data):
        """从多个来源提取设备名称"""
        # 优先从广播数据获取
        if advertisement_data:
            if hasattr(advertisement_data, 'local_name') and advertisement_data.local_name:
                return advertisement_data.local_name
        
        # 从设备对象获取
        if hasattr(device, 'name') and device.name:
            return device.name
        
        # 尝试嵌套属性
        if hasattr(device, 'device') and hasattr(device.device, 'name'):
            return device.device.name
        
        return None
    
    def get_display_name(self):
        """获取显示名称"""
        return self.name if self.name else "未知设备"


class DeviceScanThread(QThread):
    """优化的设备扫描线程"""
    
    scan_started = pyqtSignal()
    scan_finished = pyqtSignal(list)
    scan_error = pyqtSignal(str)
    device_found = pyqtSignal(object)  # 发送 DeviceInfo 对象
    device_updated = pyqtSignal(object)  # 设备信息更新
    
    def __init__(self):
        super().__init__()
        self.filter_heart_rate_devices = False
        self.scanning = False
        self.scan_duration = 30  # 缩短扫描时间到 30 秒
        self._devices = {}
    
    def stop(self):
        """停止扫描"""
        self.scanning = False
    
    def run(self):
        """执行扫描"""
        try:
            self.scanning = True
            self.scan_started.emit()
            devices = asyncio.run(self._scan_devices_async())
            self.scan_finished.emit(devices)
        except Exception as e:
            print(f"[DeviceScanThread] 扫描异常: {e}")
            self.scan_error.emit(str(e))
        finally:
            self.scanning = False
    
    async def _scan_devices_async(self):
        """异步扫描设备"""
        self._devices.clear()
        
        def detection_callback(device, advertisement_data):
            """设备发现回调"""
            if not self.scanning:
                return
            
            address = device.address
            
            if address not in self._devices:
                # 新设备
                device_info = DeviceInfo(device, advertisement_data)
                self._devices[address] = device_info
                self.device_found.emit(device_info)
                print(f"[DeviceScanThread] 发现新设备: {device_info.get_display_name()} ({address})")
            else:
                # 更新已有设备信息
                existing = self._devices[address]
                existing.device = device
                existing.advertisement_data = advertisement_data
                existing.last_seen = asyncio.get_event_loop().time()
                
                # 尝试更新名称（如果之前没有）
                if not existing.name:
                    new_name = existing._extract_name(device, advertisement_data)
                    if new_name:
                        existing.name = new_name
                        self.device_updated.emit(existing)
                        print(f"[DeviceScanThread] 更新设备名称: {existing.get_display_name()} ({address})")
        
        # 开始扫描
        scanner = BleakScanner(detection_callback=detection_callback)
        await scanner.start()
        print(f"[DeviceScanThread] 开始扫描，持续 {self.scan_duration} 秒...")
        
        # 等待扫描完成
        start_time = asyncio.get_event_loop().time()
        while self.scanning and (asyncio.get_event_loop().time() - start_time < self.scan_duration):
            await asyncio.sleep(0.1)
        
        # 停止扫描
        await scanner.stop()
        print(f"[DeviceScanThread] 扫描完成，发现 {len(self._devices)} 个设备")
        
        # 如果需要筛选心率设备
        if self.filter_heart_rate_devices:
            return await self._filter_heart_rate_devices(list(self._devices.values()))
        
        return list(self._devices.values())
    
    async def _filter_heart_rate_devices(self, devices):
        """筛选支持心率服务的设备"""
        filtered = []
        print(f"[DeviceScanThread] 开始筛选心率设备，共 {len(devices)} 个设备...")
        
        for device_info in devices:
            try:
                async with BleakClient(device_info.device, timeout=3) as client:
                    has_heart_rate = False
                    for service in client.services:
                        if HEART_RATE_SERVICE_UUID in service.uuid.lower():
                            has_heart_rate = True
                            break
                    
                    if has_heart_rate:
                        filtered.append(device_info)
                        print(f"[DeviceScanThread] 找到心率设备: {device_info.get_display_name()}")
            except Exception as e:
                print(f"[DeviceScanThread] 筛选设备失败 {device_info.address}: {e}")
                continue
        
        print(f"[DeviceScanThread] 筛选完成，找到 {len(filtered)} 个心率设备")
        return filtered


class HeartRateMonitorThread(QThread):
    """心率监测线程"""
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


class HeartRateSimulator:
    """心率数据模拟器，使用平滑随机算法"""
    
    def __init__(self, min_hr=60, max_hr=120):
        self.min_hr = min_hr
        self.max_hr = max_hr
        self.current_hr = random.randint(min_hr + 10, max_hr - 10)
        self.target_hr = self.current_hr
        self.smoothing_factor = 0.3
        
    def generate_next(self):
        """生成下一个平滑的心率值"""
        change = random.uniform(-5, 5)
        self.target_hr = max(self.min_hr, min(self.max_hr, self.target_hr + change))
        
        self.current_hr = self.current_hr + (self.target_hr - self.current_hr) * self.smoothing_factor
        
        return int(round(self.current_hr))


class HeartRateSimulatorThread(QThread):
    """模拟心率监测线程"""
    heart_rate_updated = pyqtSignal(int)
    connection_status = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.simulator = HeartRateSimulator()
        
    def run(self):
        self.running = True
        self.connection_status.emit("设备连接成功")
        self.connection_status.emit("开始心率监测")
        
        try:
            while self.running:
                hr = self.simulator.generate_next()
                self.heart_rate_updated.emit(hr)
                self.msleep(1000)
        except Exception as e:
            self.error_occurred.emit(f"模拟出错: {e}")
            
    def stop(self):
        self.running = False


def check_debug_file():
    """检查 .debug 文件是否存在"""
    debug_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".debug")
    return os.path.exists(debug_file_path)


class HeartRateMonitorCore:
    """心率监测器核心功能类"""
    
    def __init__(self, settings_manager=None):
        self.devices = []
        self.selected_device = None
        self.monitor_thread = None
        self.scan_thread = None
        self.settings_manager = settings_manager
        self.simulator_mode = False
        
        self.auto_reconnect_enabled = True
        self.max_reconnect_attempts = 5
        self.reconnect_interval = 5
        self.reconnect_attempts = 0
        
        if self.settings_manager:
            self.load_settings()
    
    def load_settings(self):
        """从设置管理器加载设置"""
        if not self.settings_manager:
            return
        
        self.auto_reconnect_enabled = self.settings_manager.get("auto_reconnect_enabled", True)
        self.max_reconnect_attempts = self.settings_manager.get("auto_reconnect_attempts", 5)
        self.reconnect_interval = self.settings_manager.get("auto_reconnect_interval", 5)
        print(f"[Core] 自动重连设置已加载: enabled={self.auto_reconnect_enabled}, attempts={self.max_reconnect_attempts}, interval={self.reconnect_interval}")
    
    def is_device_supported(self, device):
        """检查设备是否支持心率监测"""
        return True
    
    def cleanup(self):
        """清理资源"""
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.scan_thread.wait()
