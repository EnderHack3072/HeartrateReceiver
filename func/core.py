import asyncio
import os
from PyQt6.QtCore import QThread, pyqtSignal
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

timeout = 10

HEART_RATE_SERVICE_UUID = "180d"


class DeviceInfo:
    def __init__(self, device, advertisement_data=None):
        self.device = device
        self.address = device.address
        self.name = self._extract_name(device, advertisement_data)
        self.rssi = advertisement_data.rssi if advertisement_data and hasattr(advertisement_data, 'rssi') else None
        self.advertisement_data = advertisement_data
        self.last_seen = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
    
    def _extract_name(self, device, advertisement_data):
        if advertisement_data:
            if hasattr(advertisement_data, 'local_name') and advertisement_data.local_name:
                return advertisement_data.local_name
        
        if hasattr(device, 'name') and device.name:
            return device.name
        
        if hasattr(device, 'device') and hasattr(device.device, 'name'):
            return device.device.name
        
        return None
    
    def get_display_name(self):
        return self.name if self.name else "未知设备"


class DeviceScanThread(QThread):
    scan_started = pyqtSignal()
    scan_finished = pyqtSignal(list)
    scan_error = pyqtSignal(str)
    device_found = pyqtSignal(object)
    device_updated = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.filter_heart_rate_devices = False
        self.scanning = False
        self.scan_duration = 30
        self._devices = {}
    
    def stop(self):
        self.scanning = False
    
    def run(self):
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
        self._devices.clear()
        
        def detection_callback(device, advertisement_data):
            if not self.scanning:
                return
            
            address = device.address
            
            if address not in self._devices:
                device_info = DeviceInfo(device, advertisement_data)
                self._devices[address] = device_info
                self.device_found.emit(device_info)
                print(f"[DeviceScanThread] 发现新设备: {device_info.get_display_name()} ({address})")
            else:
                existing = self._devices[address]
                existing.device = device
                existing.advertisement_data = advertisement_data
                existing.last_seen = asyncio.get_event_loop().time()
                
                if not existing.name:
                    new_name = existing._extract_name(device, advertisement_data)
                    if new_name:
                        existing.name = new_name
                        self.device_updated.emit(existing)
                        print(f"[DeviceScanThread] 更新设备名称: {existing.get_display_name()} ({address})")
        
        scanner = BleakScanner(detection_callback=detection_callback)
        await scanner.start()
        print(f"[DeviceScanThread] 开始扫描，持续 {self.scan_duration} 秒...")
        
        start_time = asyncio.get_event_loop().time()
        while self.scanning and (asyncio.get_event_loop().time() - start_time < self.scan_duration):
            await asyncio.sleep(0.1)
        
        await scanner.stop()
        print(f"[DeviceScanThread] 扫描完成，发现 {len(self._devices)} 个设备")
        
        if self.filter_heart_rate_devices:
            return await self._filter_heart_rate_devices(list(self._devices.values()))
        
        return list(self._devices.values())
    
    async def _filter_heart_rate_devices(self, devices):
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


class HeartRateMonitorCore:
    def __init__(self, settings_manager=None):
        self.devices = []
        self.selected_device = None
        self.monitor_thread = None
        self.scan_thread = None
        self.settings_manager = settings_manager
        
        self.auto_reconnect_enabled = True
        self.max_reconnect_attempts = 5
        self.reconnect_interval = 5
        self.reconnect_attempts = 0
        
        if self.settings_manager:
            self.load_settings()
    
    def load_settings(self):
        if not self.settings_manager:
            return
        
        self.auto_reconnect_enabled = self.settings_manager.get("auto_reconnect_enabled", True)
        self.max_reconnect_attempts = self.settings_manager.get("auto_reconnect_attempts", 5)
        self.reconnect_interval = self.settings_manager.get("auto_reconnect_interval", 5)
        print(f"[Core] 自动重连设置已加载: enabled={self.auto_reconnect_enabled}, attempts={self.max_reconnect_attempts}, interval={self.reconnect_interval}")
    
    def is_device_supported(self, device):
        return True
    
    def cleanup(self):
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.scan_thread.wait()
