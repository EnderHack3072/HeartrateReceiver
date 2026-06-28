from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import CardWidget
from ui.charts.trend_chart.trend_line_chart import TrendLineChart


class TrendChartPage(QWidget):
    """趋势折线图页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        # 主布局
        self.trend_chart_layout = QVBoxLayout(self)
        self.trend_chart_layout.setSpacing(0)
        self.trend_chart_layout.setContentsMargins(0, 0, 0, 0)
        
        # 动态折线图卡片（与其他卡片等高）
        self.chart_card = CardWidget(self)
        self.chart_layout = QVBoxLayout(self.chart_card)
        self.chart_layout.setContentsMargins(12, 12, 12, 12)
        self.chart_layout.setSpacing(8)
        
        # 创建顶部水平布局（用于放置文本标签）
        self.top_layout = QHBoxLayout()
        self.top_layout.setSpacing(10)
        
        # 左侧文本标签
        self.left_label = QLabel("趋势")
        self.left_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 24px; font-weight: normal; color: #333;")
        self.left_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        
        # 添加文本标签
        self.top_layout.addWidget(self.left_label)
        
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
        self.trend_chart = TrendLineChart()
        self.trend_chart.setFixedHeight(180)  # 调整高度为180
        self.chart_layout.addWidget(self.trend_chart)
        
        # 创建底部水平布局（用于放置"37.5秒"和"0"）- 移到卡片内部
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(10)
        
        # 左下角文本标签："37.5秒"
        self.bottom_left_label = QLabel("0")
        self.bottom_left_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: rgb(100, 100, 100);")
        
        # 右下角文本标签："当前范围"
        self.bottom_right_label = QLabel("当前")
        self.bottom_right_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: rgb(100, 100, 100);")
        
        # 添加弹性空间，让文本标签分别靠在两侧
        self.bottom_layout.addWidget(self.bottom_left_label)
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.bottom_right_label)
        
        # 将底部布局添加到卡片布局（而不是主布局）
        self.chart_layout.addLayout(self.bottom_layout)
        
        # 将卡片添加到趋势折线图页面
        self.trend_chart_layout.addWidget(self.chart_card)
        
    def update_heart_rate(self, heart_rate):
        """更新心率数据"""
        self.trend_chart.add_value(heart_rate)
        # 更新HR显示（HR后面空两格显示数字）
        #self.left_label.setText(f"HR  {heart_rate}")
        # 更新右上角显示MAX_Y值
        self.top_right_label.setText(f"{int(self.trend_chart.MAX_Y)}")
        # 右下角始终显示0
        #self.bottom_right_label.setText("0")
