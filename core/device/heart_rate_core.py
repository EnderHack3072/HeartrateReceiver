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
