from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from qfluentwidgets import (
    CardWidget, TitleLabel, BodyLabel, SubtitleLabel,
    PushButton, PrimaryPushButton, SegmentedWidget, CheckBox, ScrollArea,
    Theme, setTheme
)

class SettingsInterface(QWidget):
    """设置界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_interface")
        self.parent = parent
        self.setup_ui()
    
    def update_settings(self):
        """更新设置状态，读取持久化数据"""
        # 重新读取关闭行为设置
        close_behavior = self.parent.settings_manager.get("close_behavior", "ask")
        if close_behavior == "close" or close_behavior == "ask":
            self.segmented_widget.setCurrentItem("close")
        elif close_behavior == "minimize":
            self.segmented_widget.setCurrentItem("minimize")
        
        # 重新读取显示关闭确认对话框设置
        show_confirmation = self.parent.settings_manager.get("show_close_confirmation", True)
        self.confirmation_checkbox.setChecked(show_confirmation)
        
        # 重新读取悬浮窗拖动功能设置
        floating_window_drag_enabled = self.parent.settings_manager.get("floating_window_drag_enabled", True)
        self.floating_window_drag_enabled_checkbox.setChecked(floating_window_drag_enabled)
        
        # 重新读取悬浮窗拖动方式设置
        drag_type = self.parent.settings_manager.get("floating_window_drag_type", "single_click")
        self.drag_type_segmented.setCurrentItem(drag_type)
        
        # 重新读取悬浮窗始终置顶设置
        always_on_top = self.parent.settings_manager.get("floating_window_always_on_top", True)
        self.always_on_top_checkbox.setChecked(always_on_top)
        
        # 重新读取主题设置
        theme = self.parent.settings_manager.get("theme", "light")
        if theme == "auto":
            # 如果之前是跟随系统，默认使用浅色主题
            theme = "light"
        self.theme_segmented.setCurrentItem(theme)
    
    def showEvent(self, event):
        """当界面显示时调用，用于更新设置状态"""
        super().showEvent(event)
        # 读取并更新设置状态
        self.update_settings()
    
    def setup_ui(self):
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(16)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建滚动区域（使用QFluentWidgets的ScrollArea，自带fluent风格滚动条）
        self.scroll_area = ScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # 设置滚动区域背景为透明，与整体界面融合
        self.scroll_area.setStyleSheet("border: none; background-color: transparent;")
        
        # 创建滚动区域的内容widget
        self.scroll_content = QWidget()
        # 设置滚动内容背景色为透明，继承父容器背景
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(16)
        # 为右侧滚动条留出空间，避免卡片内容与滚动条重叠
        self.scroll_layout.setContentsMargins(0, 0, 20, 0)
        
        # 关闭行为设置卡片
        self.close_behavior_card = CardWidget(self.scroll_content)
        self.close_behavior_layout = QVBoxLayout(self.close_behavior_card)
        self.close_behavior_layout.setSpacing(12)
        self.close_behavior_layout.setContentsMargins(20, 20, 20, 20)
        
        self.close_behavior_title = BodyLabel("关闭行为")
        
        # 分段控制器
        self.segmented_widget = SegmentedWidget(self.scroll_content)
        self.segmented_widget.addItem("close", "直接关闭")
        self.segmented_widget.addItem("minimize", "最小化到任务栏")
        
        # 设置当前选中项
        close_behavior = self.parent.settings_manager.get("close_behavior", "ask")
        if close_behavior == "close" or close_behavior == "ask":
            self.segmented_widget.setCurrentItem("close")
        elif close_behavior == "minimize":
            self.segmented_widget.setCurrentItem("minimize")
        
        # 连接分段控制器信号
        self.segmented_widget.currentItemChanged.connect(self.on_close_behavior_changed)
        
        # 显示关闭确认对话框复选框
        self.confirmation_checkbox = CheckBox("显示关闭确认对话框", self.scroll_content)
        show_confirmation = self.parent.settings_manager.get("show_close_confirmation", True)
        self.confirmation_checkbox.setChecked(show_confirmation)
        self.confirmation_checkbox.stateChanged.connect(self.on_confirmation_toggled)
        
        # 复选框布局
        self.confirmation_layout = QHBoxLayout()
        self.confirmation_layout.setAlignment(Qt.AlignRight)
        self.confirmation_layout.addWidget(self.confirmation_checkbox)
        
        # 添加控件到关闭行为卡片
        self.close_behavior_layout.addWidget(self.close_behavior_title)
        self.close_behavior_layout.addWidget(self.segmented_widget)
        self.close_behavior_layout.addLayout(self.confirmation_layout)
        
        # 将关闭行为卡片添加到滚动布局
        self.scroll_layout.addWidget(self.close_behavior_card)
        
        # 获取第一张卡片的最小高度
        # 由于第一张卡片包含标题、分段控制器和复选框，我们需要确保空卡片至少有相同的高度
        min_card_height = 180  # 根据第一张卡片的内容估算的最小高度
        
        # 添加悬浮窗设置卡片
        self.floating_window_card = CardWidget(self.scroll_content)
        self.floating_window_card.setMinimumHeight(min_card_height)
        self.floating_window_layout = QVBoxLayout(self.floating_window_card)
        self.floating_window_layout.setSpacing(12)
        self.floating_window_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        self.floating_window_title = BodyLabel("悬浮窗设置")
        self.floating_window_layout.addWidget(self.floating_window_title)
        
        # 启用悬浮窗拖动功能复选框
        self.floating_window_drag_enabled_checkbox = CheckBox("启用悬浮窗拖动功能", self.scroll_content)
        floating_window_drag_enabled = self.parent.settings_manager.get("floating_window_drag_enabled", True)
        self.floating_window_drag_enabled_checkbox.setChecked(floating_window_drag_enabled)
        self.floating_window_drag_enabled_checkbox.stateChanged.connect(self.on_floating_window_drag_enabled_toggled)
        self.floating_window_layout.addWidget(self.floating_window_drag_enabled_checkbox)
        
        # 拖动方式分段控制器
        self.drag_type_segmented = SegmentedWidget(self.scroll_content)
        self.drag_type_segmented.addItem("single_click", "单击拖动")
        self.drag_type_segmented.addItem("double_click", "双击拖动")
        
        # 设置当前选中项
        drag_type = self.parent.settings_manager.get("floating_window_drag_type", "single_click")
        self.drag_type_segmented.setCurrentItem(drag_type)
        self.drag_type_segmented.currentItemChanged.connect(self.on_drag_type_changed)
        self.floating_window_layout.addWidget(self.drag_type_segmented)
        
        # 始终置顶复选框
        self.always_on_top_checkbox = CheckBox("始终置顶", self.scroll_content)
        always_on_top = self.parent.settings_manager.get("floating_window_always_on_top", True)
        self.always_on_top_checkbox.setChecked(always_on_top)
        self.always_on_top_checkbox.stateChanged.connect(self.on_always_on_top_toggled)
        
        # 复选框布局
        self.always_on_top_layout = QHBoxLayout()
        self.always_on_top_layout.setAlignment(Qt.AlignRight)
        self.always_on_top_layout.addWidget(self.always_on_top_checkbox)
        
        self.floating_window_layout.addLayout(self.always_on_top_layout)
        
        self.scroll_layout.addWidget(self.floating_window_card)
        
        # 添加第2个空卡片，与第一张卡片大小相同
        self.empty_card2 = CardWidget(self.scroll_content)
        self.empty_card2.setMinimumHeight(min_card_height)
        self.empty_layout2 = QVBoxLayout(self.empty_card2)
        self.empty_layout2.setSpacing(12)
        self.empty_layout2.setContentsMargins(20, 20, 20, 20)
        self.empty_layout2.addWidget(BodyLabel("空卡片 3"))
        # 添加占位控件，模拟第一张卡片的高度
        spacer2 = QSpacerItem(0, 100, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.empty_layout2.addItem(spacer2)
        self.scroll_layout.addWidget(self.empty_card2)
        
        # 添加主题设置卡片
        self.theme_card = CardWidget(self.scroll_content)
        self.theme_card.setMinimumHeight(min_card_height)
        self.theme_layout = QVBoxLayout(self.theme_card)
        self.theme_layout.setSpacing(12)
        self.theme_layout.setContentsMargins(20, 20, 20, 20)
        
        # 主题设置标题
        self.theme_title = BodyLabel("主题设置")
        self.theme_layout.addWidget(self.theme_title)
        
        # 主题设置分段控制器
        self.theme_segmented = SegmentedWidget(self.scroll_content)
        self.theme_segmented.addItem("light", "浅色主题")
        self.theme_segmented.addItem("dark", "深色主题")
        
        # 设置当前选中项
        theme = self.parent.settings_manager.get("theme", "light")
        if theme == "auto":
            # 如果之前是跟随系统，默认使用浅色主题
            theme = "light"
        self.theme_segmented.setCurrentItem(theme)
        
        # 连接分段控制器信号
        self.theme_segmented.currentItemChanged.connect(self.on_theme_changed)
        
        self.theme_layout.addWidget(self.theme_segmented)
        self.scroll_layout.addWidget(self.theme_card)
        
        # 添加上下缓冲空间
        self.scroll_layout.addSpacing(20)
        
        # 设置滚动区域的内容
        self.scroll_area.setWidget(self.scroll_content)
        
        # 将滚动区域添加到主布局
        self.main_layout.addWidget(self.scroll_area)
    
    def on_close_behavior_changed(self, item):
        """关闭行为变化处理"""
        self.parent.settings_manager.set("close_behavior", item)
    
    def on_confirmation_toggled(self, state):
        """显示关闭确认对话框开关变化处理"""
        self.parent.settings_manager.set("show_close_confirmation", state == Qt.Checked)
    
    def on_floating_window_drag_enabled_toggled(self, state):
        """悬浮窗拖动功能启用状态变化处理"""
        # 更新设置并保存到文件
        is_enabled = state == Qt.CheckState.Checked
        self.parent.settings_manager.set("floating_window_drag_enabled", is_enabled)
        print(f"设置已保存：floating_window_drag_enabled = {is_enabled}")
        
        # 确保能正确访问悬浮窗实例
        if hasattr(self.parent, 'heart_rate_window') and self.parent.heart_rate_window is not None:
            # 直接更新悬浮窗的变量，确保立刻生效
            self.parent.heart_rate_window.drag_enabled = is_enabled
            print(f"悬浮窗变量已更新：drag_enabled = {is_enabled}")
    
    def on_drag_type_changed(self, item):
        """悬浮窗拖动方式变化处理"""
        # 更新设置并保存到文件
        self.parent.settings_manager.set("floating_window_drag_type", item)
        print(f"设置已保存：floating_window_drag_type = {item}")
        
        # 确保能正确访问悬浮窗实例
        if hasattr(self.parent, 'heart_rate_window') and self.parent.heart_rate_window is not None:
            # 直接更新悬浮窗的变量，确保立刻生效
            self.parent.heart_rate_window.drag_type = item
            print(f"悬浮窗变量已更新：drag_type = {item}")
    
    def on_always_on_top_toggled(self, state):
        """悬浮窗始终置顶状态变化处理"""
        # 更新设置并保存到文件
        is_always_on_top = state == Qt.CheckState.Checked
        self.parent.settings_manager.set("floating_window_always_on_top", is_always_on_top)
        print(f"设置已保存：floating_window_always_on_top = {is_always_on_top}")
        
        # 确保能正确访问悬浮窗实例
        if hasattr(self.parent, 'heart_rate_window') and self.parent.heart_rate_window is not None:
            # 直接更新悬浮窗的变量，确保立刻生效
            self.parent.heart_rate_window.always_on_top = is_always_on_top
            print(f"悬浮窗变量已更新：always_on_top = {is_always_on_top}")
            # 更新窗口标志
            self.parent.heart_rate_window.update_window_flags()
            print("悬浮窗窗口标志已更新")
    
    def on_theme_changed(self, item):
        """主题设置变化处理"""
        # 更新设置并保存到文件
        self.parent.settings_manager.set("theme", item)
        print(f"设置已保存：theme = {item}")
        
        # 根据选择的主题设置对应的主题
        if item == "light":
            setTheme(Theme.LIGHT)
            print("主题已设置为：浅色主题")
        elif item == "dark":
            setTheme(Theme.DARK)
            print("主题已设置为：深色主题")