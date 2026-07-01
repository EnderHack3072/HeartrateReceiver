from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPixmap
from collections import deque
from qfluentwidgets import CardWidget
from ui.charts.line_chart.dynamic_line_chart import DynamicLineChart


class HeartRateWindow(QMainWindow):
    """独立的心率显示窗口 - 通过信号接收数据，不直接引用 parent 内部对象"""

    def __init__(self, parent=None, settings_manager=None, signals=None):
        super().__init__(parent)
        self.setObjectName("heart_rate_window")
        self.parent_window = parent
        self.current_device_name = None
        self.settings_manager = settings_manager
        self.signals = signals

        if self.settings_manager:
            self.drag_enabled = self.settings_manager.get("floating_window_drag_enabled", True)
            self.drag_type = self.settings_manager.get("floating_window_drag_type", "single_click")
            self.always_on_top = self.settings_manager.get("floating_window_always_on_top", True)

            pos = self.settings_manager.get("floating_window_pos", {"x": 100, "y": 100})
            self.last_pos = QPoint(pos["x"], pos["y"])
        else:
            self.drag_enabled = True
            self.drag_type = "single_click"
            self.always_on_top = True
            self.last_pos = QPoint(100, 100)

        self.double_click_timer = QTimer()
        self.double_click_timer.setSingleShot(True)
        self.double_click_timer.timeout.connect(self._handle_single_click)
        self.drag_position = None
        self.is_dragging = False

        self.update_window_flags()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(400, 320)
        self.setFixedSize(self.size())

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

        if self.signals:
            self.signals.heart_rate_updated.connect(self.update_heart_rate)
            self.signals.connection_status_changed.connect(self.update_status)
            self.signals.device_connected.connect(self._on_device_connected)

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.chart_card = CardWidget(self.central_widget)
        self.chart_layout = QVBoxLayout(self.chart_card)
        self.chart_layout.setContentsMargins(20, 20, 20, 20)
        self.chart_layout.setSpacing(10)

        self.top_layout = QHBoxLayout()
        self.top_layout.setSpacing(10)

        self.left_label = QLabel("HR")
        self.left_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 28px; font-weight: normal; color: #333;")
        self.left_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        self.right_label = QLabel("请先连接设备")
        self.right_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 18px; font-weight: normal; color: #333;")
        self.right_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        self.top_layout.addWidget(self.left_label)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.right_label)

        self.chart_layout.addLayout(self.top_layout)

        self.second_row_layout = QHBoxLayout()
        self.second_row_layout.setSpacing(10)

        self.top_label = QLabel("心率")
        self.top_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: rgb(100, 100, 100);")
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.top_right_label = QLabel("当前范围")
        self.top_right_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: rgb(100, 100, 100);")
        self.top_right_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.second_row_layout.addWidget(self.top_label)
        self.second_row_layout.addStretch()
        self.second_row_layout.addWidget(self.top_right_label)

        self.chart_layout.addLayout(self.second_row_layout)

        self.chart = DynamicLineChart()
        self.chart_layout.addWidget(self.chart)

        self.main_layout.addWidget(self.chart_card)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(10)

        self.bottom_left_label = QLabel("37.5秒前")
        self.bottom_left_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: rgb(100, 100, 100);")

        self.bottom_right_label = QLabel("当前范围")
        self.bottom_right_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: rgb(100, 100, 100);")

        self.bottom_layout.addWidget(self.bottom_left_label)
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.bottom_right_label)

        self.chart_layout.addLayout(self.bottom_layout)

        self.main_layout.addWidget(self.chart_card)

    def mousePressEvent(self, event):
        if self.drag_enabled and event.button() == Qt.MouseButton.LeftButton:
            if self.drag_type == "single_click":
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                self.is_dragging = True
                event.accept()
            elif self.drag_type == "double_click":
                if self.double_click_timer.isActive():
                    self.double_click_timer.stop()
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    self.is_dragging = True
                    event.accept()
                else:
                    self.double_click_timer.start(250)

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_enabled and event.buttons() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def closeEvent(self, event):
        if self.settings_manager:
            pos = self.pos()
            self.settings_manager.set("floating_window_pos", {"x": pos.x(), "y": pos.y()})
        super().closeEvent(event)

    def _handle_single_click(self):
        pass

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        action_always_on_top = menu.addAction("始终在最前端")
        action_always_on_top.setCheckable(True)
        action_always_on_top.setChecked(self.always_on_top)

        menu.addSeparator()

        action_close = menu.addAction("关闭")

        action = menu.exec(event.globalPos())

        if action == action_always_on_top:
            self.always_on_top = action_always_on_top.isChecked()
            if self.settings_manager:
                self.settings_manager.set("floating_window_always_on_top", self.always_on_top)
            self.update_window_flags()
        elif action == action_close:
            self.close()

    def update_window_flags(self):
        if self.always_on_top:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.show()

    def reload_settings(self):
        if self.settings_manager:
            self.drag_enabled = self.settings_manager.get("floating_window_drag_enabled", True)
            self.drag_type = self.settings_manager.get("floating_window_drag_type", "single_click")
            self.always_on_top = self.settings_manager.get("floating_window_always_on_top", True)

            pos = self.settings_manager.get("floating_window_pos", {"x": 100, "y": 100})
            self.last_pos = QPoint(pos["x"], pos["y"])

            self.update_window_flags()

        print(f"悬浮窗设置已更新：拖动功能={'启用' if self.drag_enabled else '禁用'}，拖动方式={self.drag_type}，始终置顶={'是' if self.always_on_top else '否'}")

    def update_heart_rate(self, heart_rate):
        self.chart.add_value(heart_rate)
        self.left_label.setText(f"HR  {heart_rate}")
        self.top_right_label.setText(f"{int(self.chart.MAX_Y)}")
        self.bottom_right_label.setText("0")

    def _on_device_connected(self, device_name):
        """通过 device_connected 信号接收设备名称，避免穿透 parent"""
        self.current_device_name = device_name
        self.right_label.setText(device_name if device_name else "未知设备")

    def update_status(self, status):
        if "设备连接成功" in status:
            # device_name 已通过 _on_device_connected 设置
            pass
        elif "设备已断开连接" in status or "请先连接设备" in status:
            self.current_device_name = None
            self.right_label.setText("请先连接设备")
