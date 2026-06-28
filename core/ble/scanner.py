import asyncio
from PyQt6.QtCore import QThread, pyqtSignal
from bleak import BleakClient, BleakScanner

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
