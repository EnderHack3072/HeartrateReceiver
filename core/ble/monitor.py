import asyncio
import threading
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

timeout = 10


class HeartRateMonitorThread(threading.Thread):
    """使用 threading.Thread 替代 QThread 的心率监测线程"""

    def __init__(self, device, on_heart_rate_updated=None,
                 on_connection_status=None, on_error=None):
        super().__init__()
        self.daemon = True
        self.device = device
        self.running = False
        self.client = None

        # 回调函数替代 pyqtSignal
        self.on_heart_rate_updated_cb = on_heart_rate_updated
        self.on_connection_status_cb = on_connection_status
        self.on_error_cb = on_error

    def run(self):
        try:
            self.running = True
            asyncio.run(self.monitor_heart_rate())
        except Exception as e:
            if self.on_error_cb:
                self.on_error_cb(str(e))

    def stop(self):
        self.running = False

    async def monitor_heart_rate(self):
        def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
            try:
                value = int(data.hex().split('06')[1], 16)
                if self.on_heart_rate_updated_cb:
                    self.on_heart_rate_updated_cb(value)
            except Exception as e:
                if self.on_error_cb:
                    self.on_error_cb(f"解析心率数据出错: {e}")

        try:
            if self.on_connection_status_cb:
                self.on_connection_status_cb("正在连接设备...")

            def disconnected_callback(client):
                if self.on_connection_status_cb:
                    self.on_connection_status_cb("设备已断开连接")
                self.running = False

            async with BleakClient(self.device, disconnected_callback=disconnected_callback, timeout=timeout) as client:
                self.client = client
                if self.on_connection_status_cb:
                    self.on_connection_status_cb("设备连接成功")

                if self.on_connection_status_cb:
                    self.on_connection_status_cb("正在查找心率测量特征...")
                hr_measurement_uuid = None
                for service in client.services:
                    for characteristic in service.characteristics:
                        if "Heart Rate Measurement" in characteristic.description:
                            hr_measurement_uuid = characteristic.uuid
                            break
                    if hr_measurement_uuid:
                        break

                if hr_measurement_uuid:
                    if self.on_connection_status_cb:
                        self.on_connection_status_cb("开始心率监测")
                    await client.start_notify(hr_measurement_uuid, notification_handler)

                    while self.running:
                        await asyncio.sleep(0.1)

                    await client.stop_notify(hr_measurement_uuid)
                else:
                    if self.on_error_cb:
                        self.on_error_cb("未找到心率测量特征")
        except Exception as e:
            if self.on_error_cb:
                self.on_error_cb(f"连接失败: {e}")
