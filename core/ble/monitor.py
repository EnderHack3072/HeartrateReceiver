import asyncio
from PyQt6.QtCore import QThread, pyqtSignal
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

timeout = 10


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
