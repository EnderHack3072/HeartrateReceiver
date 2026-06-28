from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPixmap
from collections import deque
from qfluentwidgets import CardWidget
from ui.charts.line_chart.dynamic_line_chart import DynamicLineChart
from system.settings.settings_manager import SettingsManager


class HeartRateWindow(QMainWindow):
    """独立的心率显示窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("heart_rate_window")
        self.parent_window = parent
        self.current_device_name = None
        
        # 初始化设置管理器
        self.settings_manager = SettingsManager()
        
        # 读取悬浮窗设置
        self.drag_enabled = self.settings_manager.get("floating_window_drag_enabled", True)
        self.drag_type = self.settings_manager.get("floating_window_drag_type", "single_click")
        self.always_on_top = self.settings_manager.get("floating_window_always_on_top", True)
        
        # 读取上次位置
        pos = self.settings_manager.get("floating_window_pos", {"x": 100, "y": 100})
        self.last_pos = QPoint(pos["x"], pos["y"])
        
        # 双击拖动相关变量
        self.double_click_timer = QTimer()
        self.double_click_timer.setSingleShot(True)
        self.double_click_timer.timeout.connect(self._handle_single_click)
        self.drag_position = None
        self.is_dragging = False
        
        # 设置窗口标志
        self.update_window_flags()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(400, 320)
        self.setFixedSize(self.size())
        
        # 设置窗口位置
        self.move(self.last_pos)
        
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.central_widget.setStyleSheet("""
            #central_widget {
                background-color: white;
                border-radius: 12px;
            }
        """)
        self.setCentralWidget(self.central_widget)
        self.setup_ui()
    
    def setup_ui(self):
        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 动态折线图卡片
        self.chart_card = CardWidget(self.central_widget)
        self.chart_layout = QVBoxLayout(self.chart_card)
        self.chart_layout.setContentsMargins(20, 20, 20, 20)
        self.chart_layout.setSpacing(10)
        
        # 创建顶部水平布局（用于放置两个文本标签和关闭按钮）
        self.top_layout = QHBoxLayout()
        self.top_layout.setSpacing(10)
        
        # 左侧文本标签
        self.left_label = QLabel("HR")
        self.left_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 28px; font-weight: normal; color: #333;")
        self.left_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        
        # 右上角设备名称标签
        self.right_label = QLabel("请先连接设备")
        self.right_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 18px; font-weight: normal; color: #333;")
        self.right_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        
        # 添加弹性空间，让文本标签分别靠在两侧
        self.top_layout.addWidget(self.left_label)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.right_label)
        
        # 将顶部布局添加到卡片布局
        self.chart_layout.addLayout(self.top_layout)
        
        # 创建第二行水平布局（用于放置"心率"和"当前范围"）
        self.second_row_layout = QHBoxLayout()
        self.second_row_layout.setSpacing(10)
        
        # 左侧文本标签："心率"
        self.top_label = QLabel("心率")
        self.top_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: rgb(100, 100, 100);")
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 右侧文本标签："当前范围"
        self.top_right_label = QLabel("当前范围")
        self.top_right_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: rgb(100, 100, 100);")
        self.top_right_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 添加弹性空间，让文本标签分别靠在两侧
        self.second_row_layout.addWidget(self.top_label)
        self.second_row_layout.addStretch()
        self.second_row_layout.addWidget(self.top_right_label)
        
        # 将第二行布局添加到卡片布局
        self.chart_layout.addLayout(self.second_row_layout)
        
        # 创建动态折线图
        self.chart = DynamicLineChart()
        self.chart_layout.addWidget(self.chart)
        
        # 将卡片添加到主布局
        self.main_layout.addWidget(self.chart_card)
        
        # 创建底部水平布局（用于放置"37.5秒"和"0"）- 移到卡片内部
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(10)
        
        # 左下角文本标签："37.5秒"
        self.bottom_left_label = QLabel("37.5秒前")
        self.bottom_left_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: rgb(100, 100, 100);")
        
        # 右下角文本标签："当前范围"
        self.bottom_right_label = QLabel("当前范围")
        self.bottom_right_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: rgb(100, 100, 100);")
        
        # 添加弹性空间，让文本标签分别靠在两侧
        self.bottom_layout.addWidget(self.bottom_left_label)
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.bottom_right_label)
        
        # 将底部布局添加到卡片布局（而不是主布局）
        self.chart_layout.addLayout(self.bottom_layout)
        
        # 将卡片添加到主布局
        self.main_layout.addWidget(self.chart_card)
    
    def mousePressEvent(self, event):
        """鼠标按下事件，根据设置决定是单击拖动还是双击拖动"""
        if self.drag_enabled and event.button() == Qt.MouseButton.LeftButton:
            if self.drag_type == "single_click":
                # 单击拖动
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                self.is_dragging = True
                event.accept()
            elif self.drag_type == "double_click":
                # 双击拖动处理
                if self.double_click_timer.isActive():
                    # 第二次点击，处理双击拖动
                    self.double_click_timer.stop()
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    self.is_dragging = True
                    event.accept()
                else:
                    # 第一次点击，启动定时器等待第二次点击
                    self.double_click_timer.start(250)  # 250ms内双击有效
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.is_dragging = False
        event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.drag_enabled and event.buttons() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def closeEvent(self, event):
        """窗口关闭事件，保存窗口位置"""
        # 保存当前位置
        pos = self.pos()
        self.settings_manager.set("floating_window_pos", {"x": pos.x(), "y": pos.y()})
        super().closeEvent(event)
    
    def _handle_single_click(self):
        """处理单击事件（如果没有发生双击）"""
        # 这里可以添加单击的其他处理逻辑，如果不需要可以留空
        pass
    
    def contextMenuEvent(self, event):
        """显示右键菜单"""
        menu = QMenu(self)
        
        action_always_on_top = menu.addAction("始终在最前端")
        action_always_on_top.setCheckable(True)
        action_always_on_top.setChecked(self.always_on_top)
        
        menu.addSeparator()
        
        action_close = menu.addAction("关闭")
        
        action = menu.exec(event.globalPos())
        
        if action == action_always_on_top:
            self.always_on_top = action_always_on_top.isChecked()
            # 保存设置到设置管理器
            self.settings_manager.set("floating_window_always_on_top", self.always_on_top)
            self.update_window_flags()
        elif action == action_close:
            self.close()
    
    def update_window_flags(self):
        """更新窗口标志"""
        if self.always_on_top:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.show()
    
    def reload_settings(self):
        """重新加载设置并立刻生效"""
        # 重新读取悬浮窗设置
        self.drag_enabled = self.settings_manager.get("floating_window_drag_enabled", True)
        self.drag_type = self.settings_manager.get("floating_window_drag_type", "single_click")
        self.always_on_top = self.settings_manager.get("floating_window_always_on_top", True)
        
        # 重新读取上次位置
        pos = self.settings_manager.get("floating_window_pos", {"x": 100, "y": 100})
        self.last_pos = QPoint(pos["x"], pos["y"])
        
        # 更新窗口状态
        self.update_window_flags()
        
        # 输出调试信息
        print(f"悬浮窗设置已更新：拖动功能={'启用' if self.drag_enabled else '禁用'}，拖动方式={self.drag_type}，始终置顶={'是' if self.always_on_top else '否'}")
    
    def update_heart_rate(self, heart_rate):
        """更新心率数值"""
        # 添加到折线图，包括0值
        self.chart.add_value(heart_rate)
        # 更新HR显示（HR后面空两格显示数字）
        self.left_label.setText(f"HR  {heart_rate}")
        # 更新右上角显示MAX_Y值
        self.top_right_label.setText(f"{int(self.chart.MAX_Y)}")
        # 右下角始终显示0
        self.bottom_right_label.setText("0")

    def update_status(self, status):
        """更新状态信息"""
        if "设备连接成功" in status:
            # 从父窗口获取当前连接的设备名称
            if self.parent_window and hasattr(self.parent_window, 'core') and self.parent_window.core.selected_device:
                device_name = self.parent_window.core.selected_device.name
                if device_name:
                    self.current_device_name = device_name
                    self.right_label.setText(device_name)
                else:
                    self.right_label.setText("未知设备")
            else:
                self.right_label.setText("未知设备")
        elif "已断开连接" in status or "请先连接设备" in status:
            self.current_device_name = None
            self.right_label.setText("请先连接设备")
