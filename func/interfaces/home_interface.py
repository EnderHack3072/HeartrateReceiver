from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    CardWidget, TitleLabel, BodyLabel, SubtitleLabel,
    ComboBox, PushButton, PrimaryPushButton, IndeterminateProgressBar, ProgressBar
)

class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("home_interface")
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(16)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        self.title_label = TitleLabel("设备连接")
        self.subtitle_label = SubtitleLabel("扫描并连接您的心率监测设备")
        
        # 设备选择卡片
        self.device_card = CardWidget(self)
        self.device_layout = QVBoxLayout(self.device_card)
        self.device_layout.setSpacing(12)
        self.device_layout.setContentsMargins(20, 20, 20, 20)
        
        self.device_title = BodyLabel("设备选择")
        
        self.scan_button = PrimaryPushButton("扫描设备")
        self.scan_button.setFixedHeight(32)
        self.scan_button.clicked.connect(self.parent.start_scan)
        
        # 添加不确定进度条（默认隐藏）
        self.indeterminate_bar = IndeterminateProgressBar(start=False)
        self.indeterminate_bar.hide()
        
        # 添加普通进度条（默认显示，100%）
        self.progress_bar = ProgressBar()
        self.progress_bar.setValue(100)
        
        self.combo_box = ComboBox(self.device_card)
        self.combo_box.setPlaceholderText("请先扫描设备")
        self.combo_box.setFixedHeight(32)
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        
        self.connect_button = PushButton("连接设备")
        self.connect_button.setEnabled(False)
        self.connect_button.setFixedHeight(32)
        self.connect_button.clicked.connect(self.parent.connect_device)
        
        self.disconnect_button = PushButton("断开连接")
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.setFixedHeight(32)
        self.disconnect_button.clicked.connect(self.parent.disconnect_device)
        
        self.button_layout.addWidget(self.connect_button)
        self.button_layout.addWidget(self.disconnect_button)
        
        self.device_layout.addWidget(self.device_title)
        self.device_layout.addWidget(self.scan_button)
        self.device_layout.addWidget(self.indeterminate_bar)
        self.device_layout.addWidget(self.progress_bar)
        self.device_layout.addWidget(self.combo_box)
        self.device_layout.addLayout(self.button_layout)
        
        # 将所有控件添加到主布局
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.subtitle_label)
        self.main_layout.addWidget(self.device_card)
        self.main_layout.addStretch()