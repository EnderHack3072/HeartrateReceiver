from PyQt6.QtCore import Qt, QTimer, QByteArray
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PyQt6.QtGui import QPixmap
from qfluentwidgets import TitleLabel, CardWidget, BodyLabel
from ..resources import CP2_IMAGE
class WidgetsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widgets_interface")
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(16)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        self.title_label = TitleLabel("小组件")
        
        # 添加OBS串流卡片（卡片1）
        self.card1 = CardWidget(self)
        self.card1.setFixedHeight(120)
        self.card1.installEventFilter(self)
        
        card1_layout = QHBoxLayout(self.card1)
        card1_layout.setContentsMargins(20, 20, 20, 20)
        card1_layout.setSpacing(20)
        
        card1_text = BodyLabel("<b>桌面小组件/OBS串流</b><br>提供高度自定义功能")
        card1_text.setWordWrap(True)
        
        # 创建按钮容器和按钮
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        from qfluentwidgets import PushButton
        
        self.start_button = PushButton("启动")
        self.start_button.setFixedWidth(125)
        self.start_button.clicked.connect(self.on_start_button_clicked)
        
        self.config_button = PushButton("配置")
        self.config_button.setFixedWidth(125)
        self.config_button.clicked.connect(self.on_config_button_clicked)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.config_button)
        
        card1_layout.addWidget(card1_text, 1)
        card1_layout.addWidget(button_container)
        
        # 实时心率波动图卡片（卡片2）
        self.card2 = CardWidget(self)
        self.card2.setFixedHeight(120)
        self.card2.setCursor(Qt.CursorShape.PointingHandCursor)
        self.card2.installEventFilter(self)
        
        card2_layout = QHBoxLayout(self.card2)
        card2_layout.setContentsMargins(20, 20, 20, 20)
        card2_layout.setSpacing(20)
        
        card2_text = BodyLabel("<b>实时心率波动图<br>点击启动</b><br><span style='color: red;'>关闭在右键菜单里<br>主窗口关闭时小窗口不关闭</span>")
        card2_text.setWordWrap(True)
        
        card2_image = QLabel()
        card2_image.setFixedSize(130, 98)
        
        # 使用Base64编码的图片
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray.fromBase64(CP2_IMAGE.encode()))
        if not pixmap.isNull():
            card2_image.setPixmap(pixmap.scaled(130, 98, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        card2_image.setAlignment(Qt.AlignCenter)
        
        card2_layout.addWidget(card2_text, 1)
        card2_layout.addWidget(card2_image, 0, Qt.AlignCenter)
        
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.card1)
        self.main_layout.addWidget(self.card2)
        self.main_layout.addStretch()
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于处理卡片的点击和右键菜单"""
        if obj == self.card1:
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    # 移除showHelp功能
                    return True
                elif event.button() == Qt.MouseButton.RightButton:
                    self.show_card1_context_menu(event.globalPos())
                    return True
        elif obj == self.card2:
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.parent.open_heart_rate_window()
                    return True
                elif event.button() == Qt.RightButton:
                    self.show_card2_context_menu(event.globalPos())
                    return True
        return super().eventFilter(obj, event)
    
    def show_card1_context_menu(self, position):
        """显示卡片1的右键菜单"""
        menu = QMenu(self)
        
        # 添加菜单项
        action_settings = menu.addAction("设置")
        action_about = menu.addAction("关于")
        
        # 显示菜单并获取用户选择
        action = menu.exec(position)
        
        if action == action_settings:
            print("打开OBS串流设置")
        elif action == action_about:
            print("显示OBS串流关于信息")
    
    def show_card2_context_menu(self, position):
        """显示卡片2的右键菜单"""
        menu = QMenu(self)
        
        # 添加菜单项
        action_settings = menu.addAction("设置")
        action_about = menu.addAction("关于")
        
        # 显示菜单并获取用户选择
        action = menu.exec(position)
        
        if action == action_settings:
            print("打开设置")
        elif action == action_about:
            print("显示关于信息")
    
    def on_start_button_clicked(self):
        """启动按钮点击事件"""
        print("启动OBS串流功能")
    
    def on_config_button_clicked(self):
        """配置按钮点击事件"""
        print("打开OBS串流配置")