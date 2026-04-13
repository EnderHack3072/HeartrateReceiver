import os
import shutil
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPainterPath, QIcon
from qfluentwidgets import CardWidget, SubtitleLabel, BodyLabel, PushButton, CheckBox

class StorageBar(QFrame):
    def __init__(self, segments=None, parent=None):
        super().__init__(parent)
        self.segments = segments or []
        self.setFixedHeight(20)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        radius = 4
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(230, 230, 230)))
        painter.drawRoundedRect(0, 0, width, height, radius, radius)
        
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, width, height), radius, radius)
        painter.setClipPath(path)
        
        current_x = 0
        for i, segment in enumerate(self.segments):
            seg_percent = segment.get('percent', 0)
            seg_color = segment.get('color', QColor(0, 159, 170))
            seg_width = int(width * seg_percent / 100)
            
            if seg_width > 0:
                painter.setBrush(QBrush(seg_color))
                painter.drawRect(current_x, 0, seg_width, height)
                current_x += seg_width

class StoragePage(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("storagePage")
        
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(10)
        
        self.leftLayout = QVBoxLayout()
        self.leftLayout.setSpacing(10)
        
        self.card1 = CardWidget(self)
        self.card1Layout = QVBoxLayout(self.card1)
        self.card1Layout.setContentsMargins(15, 12, 15, 12)
        self.card1Layout.setSpacing(8)
        
        self.card1HeaderLayout = QHBoxLayout()
        self.card1Title = SubtitleLabel("占用空间", self.card1)
        self.card1HeaderLayout.addWidget(self.card1Title)
        self.card1HeaderLayout.addStretch()
        
        total_space, used_space, used_percent = self._get_disk_space_info()
        self.card1TotalSpace = BodyLabel(f"共 {total_space} GB", self.card1)
        self.card1TotalSpace.setStyleSheet("font-weight: bold;")
        self.card1HeaderLayout.addWidget(self.card1TotalSpace)
        
        self.card1Layout.addLayout(self.card1HeaderLayout)
        
        app_size_gb, app_percent = self._get_app_size_info(total_space)
        orange_percent = app_percent
        cyan_percent = used_percent - app_percent
        segments = [
            {'percent': orange_percent, 'color': QColor(255, 165, 0)},
            {'percent': cyan_percent, 'color': QColor(0, 159, 170)}
        ]
        self.storageBar = StorageBar(segments, self.card1)
        self.card1Layout.addWidget(self.storageBar)
        
        from PyQt6.QtWidgets import QLabel
        self.card1InfoLayout = QHBoxLayout()
        other_data_gb = round(used_space - app_size_gb, 1)
        free_space = round(total_space - used_space, 1)
        
        self.appLabel = QLabel(f"软件占用 {app_size_gb} GB  ", self.card1)
        self.appLabel.setStyleSheet("color: #FFA500;")
        
        self.otherLabel = QLabel(f"其他数据 {other_data_gb} GB  ", self.card1)
        self.otherLabel.setStyleSheet("color: #009FAA;")
        
        self.freeLabel = QLabel(f"可用 {free_space} GB", self.card1)
        self.freeLabel.setStyleSheet("color: gray;")
        
        self.card1InfoLayout.addWidget(self.appLabel)
        self.card1InfoLayout.addWidget(self.otherLabel)
        self.card1InfoLayout.addWidget(self.freeLabel)
        self.card1Layout.addLayout(self.card1InfoLayout)
        
        self.card1Layout.addSpacing(8)
        
        self.extraLabel = QLabel("*软件本身占用很小 占用全部来自数据 条形图显示不了很正常", self.card1)
        self.card1Layout.addWidget(self.extraLabel)
        
        self.card1Layout.addStretch()
        
        self.leftLayout.addWidget(self.card1)
        
        self.card2 = CardWidget(self)
        self.card2Layout = QVBoxLayout(self.card2)
        self.card2Layout.setContentsMargins(15, 12, 15, 12)
        self.card2Layout.setSpacing(8)
        
        self.card2Title = SubtitleLabel("数据管理", self.card2)
        self.card2Layout.addWidget(self.card2Title)
        
        self.card2Content = BodyLabel("这里显示你所有的心率数据文件", self.card2)
        self.card2Layout.addWidget(self.card2Content)
        
        # 添加ListWidget
        from qfluentwidgets import ListWidget
        self.listWidget = ListWidget(self.card2)
        
        # 设置右键单击选中
        self.listWidget.setSelectRightClickedRow(True)
        
        # 添加文件信息标签
        self.fileInfoLabel = BodyLabel("", self.card2)
        
        # 添加清理建议布局
        self.cleanLayout = QHBoxLayout()
        self.cleanLabel = BodyLabel("", self.card2)
        self.cleanButton = PushButton("立即清理", self.card2)
        self.cleanButton.clicked.connect(self.clean_small_files)
        
        self.cleanLayout.addWidget(self.cleanLabel)
        self.cleanLayout.addStretch()
        self.cleanLayout.addWidget(self.cleanButton)
        
        # 初始化定时器，每5秒刷新一次列表
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_file_list)
        self.timer.start(5000)  # 5秒刷新一次
        
        # 初始刷新一次列表
        self.refresh_file_list()
        
        # 添加“每次启动时检查并清理”勾选框
        self.autoCleanCheckBox = CheckBox("每次启动时检查并清理", self.card2)
        # 从设置管理器获取初始状态
        from func.settings_manager import SettingsManager
        self.settings_manager = SettingsManager()
        self.autoCleanCheckBox.setChecked(self.settings_manager.get("auto_clean_on_startup", True))
        # 连接信号，当状态改变时更新设置
        self.autoCleanCheckBox.stateChanged.connect(self.on_auto_clean_checkbox_changed)
        
        self.card2Layout.addWidget(self.listWidget)
        self.card2Layout.addWidget(self.fileInfoLabel)
        self.card2Layout.addLayout(self.cleanLayout)
        self.card2Layout.addWidget(self.autoCleanCheckBox)
        
        self.card2Layout.addStretch()
        
        self.leftLayout.addWidget(self.card2)
        
        # 右侧布局
        self.rightLayout = QVBoxLayout()
        self.rightLayout.setSpacing(10)
        
        # 右上方卡片
        self.card4 = CardWidget(self)
        self.card4Layout = QVBoxLayout(self.card4)
        self.card4Layout.setContentsMargins(15, 12, 15, 12)
        self.card4Layout.setSpacing(8)
        
        self.card4Title = SubtitleLabel("456", self.card4)
        self.card4Layout.addWidget(self.card4Title)
        
        self.card4Layout.addStretch()
        
        # 右下角卡片
        self.card3 = CardWidget(self)
        self.card3Layout = QVBoxLayout(self.card3)
        self.card3Layout.setContentsMargins(15, 12, 15, 12)
        self.card3Layout.setSpacing(8)
        
        self.card3Title = SubtitleLabel("存储设置与优化", self.card3)
        self.card3Layout.addWidget(self.card3Title)
        
        self.card3Layout.addStretch()
        
        self.rightLayout.addWidget(self.card4)
        self.rightLayout.addStretch()
        self.rightLayout.addWidget(self.card3)
        
        self.mainLayout.addLayout(self.leftLayout, 1)
        self.mainLayout.addLayout(self.rightLayout, 1)
    
    def _get_disk_space_info(self):
        try:
            app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            total, used, free = shutil.disk_usage(app_path)
            total_gb = round(total / (1024 ** 3), 1)
            used_gb = round(used / (1024 ** 3), 1)
            used_percent = round(used / total * 100, 1) if total > 0 else 0
            return total_gb, used_gb, used_percent
        except Exception as e:
            print(f"[StoragePage] 获取磁盘空间失败: {e}")
            return 0, 0, 0
    
    def _get_app_size_info(self, total_gb):
        try:
            app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            app_size = self._get_dir_size(app_path)
            app_size_gb = round(app_size / (1024 ** 3), 2)
            app_percent = round(app_size_gb / total_gb * 100, 1) if total_gb > 0 else 0
            return app_size_gb, app_percent
        except Exception as e:
            print(f"[StoragePage] 获取软件大小失败: {e}")
            return 0, 0
    
    def _get_dir_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    if os.path.exists(filepath) and not os.path.islink(filepath):
                        total_size += os.path.getsize(filepath)
                except Exception:
                    pass
        return total_size
    
    def refresh_file_list(self):
        """刷新文件列表"""
        # 清空现有列表
        self.listWidget.clear()
        
        # 构建data文件夹路径（相对路径）
        data_dir = os.path.join('data')
        
        try:
            # 检查data文件夹是否存在
            if os.path.exists(data_dir) and os.path.isdir(data_dir):
                # 获取data文件夹中的所有文件
                files = os.listdir(data_dir)
                
                # 添加文件到列表
                for file in files:
                    item = QListWidgetItem(file)
                    self.listWidget.addItem(item)
                
                # 计算文件数量和总占用空间，以及小于5KB的文件数量
                file_count = len(files)
                total_size = 0
                small_files_count = 0
                
                # 找出最新的文件（基于文件名排序）
                latest_file = None
                if files:
                    # 按文件名排序，假设文件名包含时间戳且越新的文件名越大
                    sorted_files = sorted(files, reverse=True)
                    latest_file = sorted_files[0]
                
                for file in files:
                    # 跳过最新的文件，无论其大小如何
                    if file == latest_file:
                        file_path = os.path.join(data_dir, file)
                        if os.path.isfile(file_path):
                            try:
                                file_size = os.path.getsize(file_path)
                                total_size += file_size
                            except Exception:
                                pass
                        continue
                        
                    file_path = os.path.join(data_dir, file)
                    if os.path.isfile(file_path):
                        try:
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            if file_size < 5 * 1024:  # 小于5KB
                                small_files_count += 1
                        except Exception:
                            pass
                
                # 自动单位换算
                if total_size < 1024:
                    size_str = f"{total_size} B"
                elif total_size < 1024 * 1024:
                    size_str = f"{total_size / 1024:.2f} KB"
                elif total_size < 1024 * 1024 * 1024:
                    size_str = f"{total_size / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
                
                # 更新文件信息标签
                self.fileInfoLabel.setText(f"共{file_count}个文件，占用{size_str}磁盘空间")
                
                # 更新清理建议标签
                self.cleanLabel.setText(f"检测到{small_files_count}个建议清理的文件")
            else:
                # 如果data文件夹不存在，显示提示
                item = QListWidgetItem("data文件夹不存在")
                self.listWidget.addItem(item)
                self.fileInfoLabel.setText("")
                self.cleanLabel.setText("")
        except Exception as e:
            # 处理异常
            item = QListWidgetItem(f"获取文件列表失败: {e}")
            self.listWidget.addItem(item)
            self.fileInfoLabel.setText("")
            self.cleanLabel.setText("")
    
    def on_auto_clean_checkbox_changed(self, state):
        """处理自动清理勾选框状态改变"""
        # 更新设置
        self.settings_manager.set("auto_clean_on_startup", state == 2)  # 2表示勾选状态
    
    def clean_small_files(self):
        """清理小于5KB的文件"""
        # 构建data文件夹路径（相对路径）
        data_dir = os.path.join('data')
        
        try:
            # 检查data文件夹是否存在
            if os.path.exists(data_dir) and os.path.isdir(data_dir):
                # 获取data文件夹中的所有文件
                files = os.listdir(data_dir)
                cleaned_count = 0
                
                # 找出最新的文件（基于文件名排序）
                latest_file = None
                if files:
                    # 按文件名排序，假设文件名包含时间戳且越新的文件名越大
                    sorted_files = sorted(files, reverse=True)
                    latest_file = sorted_files[0]
                
                # 清理小于5KB的文件，跳过最新的文件
                for file in files:
                    # 跳过最新的文件，无论其大小如何
                    if file == latest_file:
                        continue
                        
                    file_path = os.path.join(data_dir, file)
                    if os.path.isfile(file_path):
                        try:
                            file_size = os.path.getsize(file_path)
                            if file_size < 5 * 1024:  # 小于5KB
                                os.remove(file_path)
                                cleaned_count += 1
                        except Exception:
                            pass
                
                # 刷新文件列表
                self.refresh_file_list()
        except Exception as e:
            print(f"清理文件失败: {e}")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        page_width = self.width()
        page_height = self.height()
        card_width = page_width // 2 - 20
        card1_height = card_width // 3
        available_height = page_height - 40 - 10 - card1_height  # 40: top+bottom margins, 10: spacing
        
        self.card1.setFixedSize(card_width, card1_height)
        if available_height > 0:
            self.card2.setFixedSize(card_width, available_height)
        else:
            self.card2.setFixedSize(card_width, 100)  # minimum height
        
        # 设置卡片3的大小为右半页的一半
        total_right_height = page_height - 40  # 40: top+bottom margins
        card3_height = total_right_height / 2
        self.card3.setFixedSize(card_width, card3_height)
        
        # 计算卡片4的高度，占满剩余空间
        card4_height = total_right_height - card3_height - 10  # 10: spacing
        if card4_height > 0:
            self.card4.setFixedSize(card_width, card4_height)
        else:
            self.card4.setFixedSize(card_width, 100)  # minimum height
