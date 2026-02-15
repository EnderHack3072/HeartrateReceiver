import json
import os

class SettingsManager:
    """设置管理器，用于持久化存储用户设置"""
    
    def __init__(self):
        # 获取应用程序数据目录
        self.settings_dir = os.path.join(os.path.expanduser("~"), ".heartrate_monitor")
        self.settings_file = os.path.join(self.settings_dir, "settings.json")
        
        # 默认设置
        self.default_settings = {
            "close_behavior": "ask",  # "ask", "minimize", "close"
            "show_close_confirmation": True,
            # 悬浮窗设置
            "floating_window_drag_enabled": True,  # 是否启用悬浮窗拖动功能
            "floating_window_drag_type": "single_click",  # "single_click" 或 "double_click"
            "floating_window_always_on_top": True,  # 是否始终置顶
            "floating_window_pos": {"x": 100, "y": 100},  # 悬浮窗上次位置
            # 自动重连设置
            "auto_reconnect_enabled": True,  # 是否启用自动重连
            "auto_reconnect_attempts": 5,  # 最大重连尝试次数
            "auto_reconnect_interval": 5,  # 重连间隔（秒）
            # 大数字卡片设置
            "big_number_font_family": "Segoe UI",  # 大数字卡片字体家族
            "big_number_font_color": "#333"  # 大数字卡片字体颜色
        }
        
        # 确保设置目录存在
        if not os.path.exists(self.settings_dir):
            os.makedirs(self.settings_dir)
        
        # 加载设置
        self.settings = self.load_settings()
    
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)
                # 合并默认设置和加载的设置
                return {**self.default_settings, **loaded_settings}
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"加载设置失败: {e}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """保存设置"""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def get(self, key, default=None):
        """获取设置值"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """设置设置值"""
        self.settings[key] = value
        self.save_settings()
    
    def reset(self):
        """重置设置为默认值"""
        self.settings = self.default_settings.copy()
        self.save_settings()