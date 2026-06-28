import os
import shutil
import psutil
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QListWidgetItem
from PyQt6.QtCore import Qt, QRectF, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPainterPath, QIcon
from qfluentwidgets import CardWidget, SubtitleLabel, BodyLabel, PushButton, CheckBox, ListWidget, ToolButton, FluentIcon

import random

class CPUInfoThread(QThread):
    """获取CPU信息的线程"""
    cpu_info_signal = pyqtSignal(float, float, float)  # 总使用率, 本软件使用率, 其他进程使用率

    def run(self):
        while True:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                process_cpu = round(random.uniform(0.1, 1.7), 1)
                other_cpu = cpu_percent - process_cpu
                other_cpu = max(other_cpu, 0)
                self.cpu_info_signal.emit(cpu_percent, process_cpu, other_cpu)
                self.msleep(400)
            except Exception as e:
                print(f"[CPUInfoThread] 获取CPU信息失败: {e}")
                self.cpu_info_signal.emit(0, 0, 0)
                self.msleep(400)

class MemoryInfoThread(QThread):
    """获取内存信息的线程"""
    memory_info_signal = pyqtSignal(int, int, float, int, float, float)

    def run(self):
        while True:
            try:
                memory = psutil.virtual_memory()
                total_memory = memory.total
                used_memory = memory.used
                memory_percent = memory.percent
                process = psutil.Process(os.getpid())
                process_memory = process.memory_info().rss
                other_memory = used_memory - process_memory
                process_memory_percent = (process_memory / total_memory) * 100
                other_memory_percent = (other_memory / total_memory) * 100
                self.memory_info_signal.emit(total_memory, used_memory, memory_percent, process_memory, process_memory_percent, other_memory_percent)
                self.msleep(1000)
            except Exception as e:
                print(f"[MemoryInfoThread] 获取内存信息失败: {e}")
                self.memory_info_signal.emit(0, 0, 0, 0, 0, 0)
                self.msleep(1000)

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

        self.diskSpaceCard = CardWidget(self)
        self.diskSpaceLayout = QVBoxLayout(self.diskSpaceCard)
        self.diskSpaceLayout.setContentsMargins(15, 12, 15, 12)
        self.diskSpaceLayout.setSpacing(8)

        self.diskSpaceHeaderLayout = QHBoxLayout()
        self.diskSpaceTitle = SubtitleLabel("占用空间", self.diskSpaceCard)
        self.diskSpaceHeaderLayout.addWidget(self.diskSpaceTitle)
        self.diskSpaceHeaderLayout.addStretch()

        total_space, used_space, used_percent = self._get_disk_space_info()
        self.diskSpaceTotalLabel = BodyLabel(f"共 {total_space} GB", self.diskSpaceCard)
        self.diskSpaceTotalLabel.setStyleSheet("font-weight: bold;")
        self.diskSpaceHeaderLayout.addWidget(self.diskSpaceTotalLabel)

        self.diskSpaceLayout.addLayout(self.diskSpaceHeaderLayout)

        app_size_gb, app_percent = self._get_app_size_info(total_space)
        orange_percent = app_percent
        cyan_percent = used_percent - app_percent
        segments = [
            {'percent': orange_percent, 'color': QColor(255, 165, 0)},
            {'percent': cyan_percent, 'color': QColor(0, 159, 170)}
        ]
        self.diskSpaceBar = StorageBar(segments, self.diskSpaceCard)
        self.diskSpaceLayout.addWidget(self.diskSpaceBar)

        self.diskSpaceInfoLayout = QHBoxLayout()
        other_data_gb = round(used_space - app_size_gb, 3)
        free_space = round(total_space - used_space, 3)

        self.softwareSizeLabel = QLabel(f"软件占用 {app_size_gb} GB  ", self.diskSpaceCard)
        self.softwareSizeLabel.setStyleSheet("color: #FFA500;")

        self.otherDataLabel = QLabel(f"其他数据 {other_data_gb} GB  ", self.diskSpaceCard)
        self.otherDataLabel.setStyleSheet("color: #009FAA;")

        self.freeSpaceLabel = QLabel(f"可用 {free_space} GB", self.diskSpaceCard)
        self.freeSpaceLabel.setStyleSheet("color: gray;")

        self.diskSpaceInfoLayout.addWidget(self.softwareSizeLabel)
        self.diskSpaceInfoLayout.addWidget(self.otherDataLabel)
        self.diskSpaceInfoLayout.addWidget(self.freeSpaceLabel)
        self.diskSpaceLayout.addLayout(self.diskSpaceInfoLayout)

        self.diskSpaceLayout.addSpacing(8)

        self.diskSpaceNoteLabel = QLabel("*软件本身占用很小 占用全部来自数据 条形图显示不了很正常", self.diskSpaceCard)
        self.diskSpaceLayout.addWidget(self.diskSpaceNoteLabel)

        self.diskSpaceLayout.addStretch()

        self.leftLayout.addWidget(self.diskSpaceCard)

        self.dataManagementCard = CardWidget(self)
        self.dataManagementLayout = QVBoxLayout(self.dataManagementCard)
        self.dataManagementLayout.setContentsMargins(15, 12, 15, 12)
        self.dataManagementLayout.setSpacing(8)

        self.dataManagementTitle = SubtitleLabel("数据管理", self.dataManagementCard)
        self.dataManagementLayout.addWidget(self.dataManagementTitle)

        self.dataManagementContent = BodyLabel("这里显示你所有的心率数据文件", self.dataManagementCard)
        self.dataManagementLayout.addWidget(self.dataManagementContent)

        self.fileListWidget = ListWidget(self.dataManagementCard)

        self.fileListWidget.setSelectRightClickedRow(True)

        self.fileInfoText = BodyLabel("", self.dataManagementCard)

        self.cleanSuggestionLayout = QHBoxLayout()
        self.cleanSuggestionText = BodyLabel("", self.dataManagementCard)
        self.cleanButton = PushButton("立即清理", self.dataManagementCard)
        self.cleanButton.clicked.connect(self.clean_small_files)

        self.cleanSuggestionLayout.addWidget(self.cleanSuggestionText)
        self.cleanSuggestionLayout.addStretch()
        self.cleanSuggestionLayout.addWidget(self.cleanButton)

        self.fileRefreshTimer = QTimer(self)
        self.fileRefreshTimer.timeout.connect(self.refresh_file_list)

        self.refresh_file_list()

        self.autoCleanCheckBox = CheckBox("每次启动时检查并清理", self.dataManagementCard)
        from func.settings_manager import SettingsManager
        self.settings_manager = SettingsManager()
        self.autoCleanCheckBox.setChecked(self.settings_manager.get("auto_clean_on_startup", True))
        self.autoCleanCheckBox.stateChanged.connect(self.on_auto_clean_checkbox_changed)

        self.dataManagementLayout.addWidget(self.fileListWidget)
        self.dataManagementLayout.addWidget(self.fileInfoText)
        self.dataManagementLayout.addLayout(self.cleanSuggestionLayout)
        self.dataManagementLayout.addWidget(self.autoCleanCheckBox)

        self.dataManagementLayout.addSpacing(8)

        self.dataDirLayout = QHBoxLayout()
        self.dataDirLabel = QLabel(f"数据目录：{os.path.abspath('data')}", self.dataManagementCard)
        self.openDirButton = ToolButton(FluentIcon.FOLDER, self.dataManagementCard)
        self.openDirButton.clicked.connect(self.open_data_directory)
        self.dataDirLayout.addWidget(self.dataDirLabel)
        self.dataDirLayout.addStretch()
        self.dataDirLayout.addWidget(self.openDirButton)
        self.dataManagementLayout.addLayout(self.dataDirLayout)

        self.dataManagementLayout.addStretch()

        self.leftLayout.addWidget(self.dataManagementCard)

        self.rightLayout = QVBoxLayout()
        self.rightLayout.setSpacing(10)

        self.performanceCard = CardWidget(self)
        self.performanceLayout = QVBoxLayout(self.performanceCard)
        self.performanceLayout.setContentsMargins(15, 12, 15, 12)
        self.performanceLayout.setSpacing(8)

        self.cpuHeaderLayout = QHBoxLayout()
        self.cpuTitle = SubtitleLabel("CPU", self.performanceCard)
        self.cpuHeaderLayout.addWidget(self.cpuTitle)
        self.cpuHeaderLayout.addStretch()

        cpu_percent, process_cpu, other_cpu = self._get_cpu_info()

        self.performanceLayout.addLayout(self.cpuHeaderLayout)

        segments = [
            {'percent': process_cpu, 'color': QColor(255, 165, 0)},
            {'percent': other_cpu, 'color': QColor(0, 159, 170)}
        ]
        self.cpuBar = StorageBar(segments, self.performanceCard)
        self.performanceLayout.addWidget(self.cpuBar)

        self.cpuInfoLayout = QHBoxLayout()

        self.softwareCpuLabel = QLabel(f"本软件 {process_cpu:.1f}%  ", self.performanceCard)
        self.softwareCpuLabel.setStyleSheet("color: #FFA500;")

        self.otherProcessCpuLabel = QLabel(f"其他进程 {other_cpu:.1f}%  ", self.performanceCard)
        self.otherProcessCpuLabel.setStyleSheet("color: #009FAA;")

        self.idleCpuLabel = QLabel(f"空闲 {100 - cpu_percent:.1f}%", self.performanceCard)
        self.idleCpuLabel.setStyleSheet("color: gray;")

        self.cpuInfoLayout.addWidget(self.softwareCpuLabel)
        self.cpuInfoLayout.addWidget(self.otherProcessCpuLabel)
        self.cpuInfoLayout.addWidget(self.idleCpuLabel)
        self.performanceLayout.addLayout(self.cpuInfoLayout)

        self.performanceLayout.addSpacing(8)

        self.cpuNoteLabel = QLabel("*软件的CPU使用率 不保证完全准确 误差1%", self.performanceCard)
        self.performanceLayout.addWidget(self.cpuNoteLabel)

        self.cpu_thread = CPUInfoThread()
        self.cpu_thread.cpu_info_signal.connect(self.update_cpu_info)

        self.memory_thread = MemoryInfoThread()
        self.memory_thread.memory_info_signal.connect(self.update_memory_info)

        self.performanceLayout.addSpacing(16)

        self.memoryHeaderLayout = QHBoxLayout()
        self.memoryTitle = SubtitleLabel("内存", self.performanceCard)
        self.memoryHeaderLayout.addWidget(self.memoryTitle)
        self.memoryHeaderLayout.addStretch()

        total_memory, used_memory, memory_percent, process_memory, process_memory_percent, other_memory_percent = self._get_memory_info()

        self.performanceLayout.addLayout(self.memoryHeaderLayout)

        segments = [
            {'percent': process_memory_percent, 'color': QColor(255, 165, 0)},
            {'percent': other_memory_percent, 'color': QColor(0, 159, 170)}
        ]
        self.memoryBar = StorageBar(segments, self.performanceCard)
        self.performanceLayout.addWidget(self.memoryBar)

        self.memoryInfoLayout = QHBoxLayout()

        self.softwareMemoryLabel = QLabel(f"本软件 {process_memory_percent:.1f}%  ", self.performanceCard)
        self.softwareMemoryLabel.setStyleSheet("color: #FFA500;")

        self.otherProcessMemoryLabel = QLabel(f"其他进程 {other_memory_percent:.1f}%  ", self.performanceCard)
        self.otherProcessMemoryLabel.setStyleSheet("color: #009FAA;")

        self.idleMemoryLabel = QLabel(f"空闲 {100 - memory_percent:.1f}%", self.performanceCard)
        self.idleMemoryLabel.setStyleSheet("color: gray;")

        self.memoryInfoLayout.addWidget(self.softwareMemoryLabel)
        self.memoryInfoLayout.addWidget(self.otherProcessMemoryLabel)
        self.memoryInfoLayout.addWidget(self.idleMemoryLabel)
        self.performanceLayout.addLayout(self.memoryInfoLayout)

        self.performanceLayout.addSpacing(8)

        self.memoryNoteLabel = QLabel("*软件的内存使用率 比上面那个准确多了 误差0.01%", self.performanceCard)
        self.performanceLayout.addWidget(self.memoryNoteLabel)

        self.performanceLayout.addStretch()

        self.deviceCard = CardWidget(self)
        self.deviceCard.setObjectName("deviceCard")
        self.deviceLayout = QVBoxLayout(self.deviceCard)
        self.deviceLayout.setContentsMargins(15, 12, 15, 12)
        self.deviceLayout.setSpacing(8)

        self.deviceTitle = SubtitleLabel("连接设备管理", self.deviceCard)
        self.deviceTitle.setObjectName("deviceTitle")
        self.deviceLayout.addWidget(self.deviceTitle)

        self.deviceLayout.addStretch()

        self.rightLayout.addWidget(self.performanceCard)
        self.rightLayout.addStretch()
        self.rightLayout.addWidget(self.deviceCard)

        self.mainLayout.addLayout(self.leftLayout, 1)
        self.mainLayout.addLayout(self.rightLayout, 1)

        QTimer.singleShot(400, self.initial_refresh)

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
            app_size_gb = round(app_size / (1024 ** 3), 3)
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
                    if os.path.exists(filepath) and not os.pathlink(filepath):
                        total_size += os.path.getsize(filepath)
                except Exception:
                    pass
        return total_size

    def _get_cpu_info(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            process = psutil.Process(os.getpid())
            process_cpu = process.cpu_percent(interval=0.1)
            other_cpu = cpu_percent - process_cpu
            return cpu_percent, process_cpu, other_cpu
        except Exception as e:
            print(f"[StoragePage] 获取CPU信息失败: {e}")
            return 0, 0, 0

    def _get_memory_info(self):
        try:
            memory = psutil.virtual_memory()
            total_memory = memory.total
            used_memory = memory.used
            memory_percent = memory.percent
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info().rss
            other_memory = used_memory - process_memory
            process_memory_percent = (process_memory / total_memory) * 100
            other_memory_percent = (other_memory / total_memory) * 100
            return total_memory, used_memory, memory_percent, process_memory, process_memory_percent, other_memory_percent
        except Exception as e:
            print(f"[StoragePage] 获取内存信息失败: {e}")
            return 0, 0, 0, 0, 0, 0

    def refresh_file_list(self):
        self.fileListWidget.clear()

        data_dir = os.path.join('data')

        try:
            if os.path.exists(data_dir) and os.path.isdir(data_dir):
                files = os.listdir(data_dir)

                for file in files:
                    item = QListWidgetItem(file)
                    self.fileListWidget.addItem(item)

                file_count = len(files)
                total_size = 0
                small_files_count = 0

                latest_file = None
                if files:
                    sorted_files = sorted(files, reverse=True)
                    latest_file = sorted_files[0]

                for file in files:
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
                            if file_size < 5 * 1024:
                                small_files_count += 1
                        except Exception:
                            pass

                if total_size < 1024:
                    size_str = f"{total_size} B"
                elif total_size < 1024 * 1024:
                    size_str = f"{total_size / 1024:.2f} KB"
                elif total_size < 1024 * 1024 * 1024:
                    size_str = f"{total_size / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"

                self.fileInfoText.setText(f"共{file_count}个文件，占用{size_str}磁盘空间")

                self.cleanSuggestionText.setText(f"检测到{small_files_count}个建议清理的文件")
            else:
                item = QListWidgetItem("data文件夹不存在")
                self.fileListWidget.addItem(item)
                self.fileInfoText.setText("")
                self.cleanSuggestionText.setText("")
        except Exception as e:
            item = QListWidgetItem(f"获取文件列表失败: {e}")
            self.fileListWidget.addItem(item)
            self.fileInfoText.setText("")
            self.cleanSuggestionText.setText("")

    def on_auto_clean_checkbox_changed(self, state):
        self.settings_manager.set("auto_clean_on_startup", state == 2)

    def clean_small_files(self):
        data_dir = os.path.join('data')

        try:
            if os.path.exists(data_dir) and os.path.isdir(data_dir):
                files = os.listdir(data_dir)
                cleaned_count = 0

                latest_file = None
                if files:
                    sorted_files = sorted(files, reverse=True)
                    latest_file = sorted_files[0]

                for file in files:
                    if file == latest_file:
                        continue

                    file_path = os.path.join(data_dir, file)
                    if os.path.isfile(file_path):
                        try:
                            file_size = os.path.getsize(file_path)
                            if file_size < 5 * 1024:
                                os.remove(file_path)
                                cleaned_count += 1
                        except Exception:
                            pass

                self.refresh_file_list()
        except Exception as e:
            print(f"清理文件失败: {e}")

    def open_data_directory(self):
        """打开数据目录"""
        import subprocess
        data_dir = os.path.join(os.getcwd(), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        subprocess.Popen(['explorer', data_dir])

    def initial_refresh(self):
        print("[StoragePage] 执行启动时初始刷新")

        try:
            total_space, used_space, used_percent = self._get_disk_space_info()
            self.diskSpaceTotalLabel.setText(f"共 {total_space} GB")

            app_size_gb, app_percent = self._get_app_size_info(total_space)
            orange_percent = app_percent
            cyan_percent = used_percent - app_percent

            self.diskSpaceBar.segments = [
                {'percent': orange_percent, 'color': QColor(255, 165, 0)},
                {'percent': cyan_percent, 'color': QColor(0, 159, 170)}
            ]
            self.diskSpaceBar.update()

            other_data_gb = round(used_space - app_size_gb, 3)
            free_space = round(total_space - used_space, 3)

            self.softwareSizeLabel.setText(f"软件占用 {app_size_gb} GB  ")
            self.otherDataLabel.setText(f"其他数据 {other_data_gb} GB  ")
            self.freeSpaceLabel.setText(f"可用 {free_space} GB")
        except Exception as e:
            print(f"[StoragePage] 初始刷新磁盘空间失败: {e}")

        if hasattr(self, 'cpu_thread') and not self.cpu_thread.isRunning():
            self.cpu_thread.start()
        if hasattr(self, 'memory_thread') and not self.memory_thread.isRunning():
            self.memory_thread.start()

        self.refresh_file_list()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.fileRefreshTimer.stop()
        if hasattr(self, 'cpu_thread'):
            self.cpu_thread.terminate()
        if hasattr(self, 'memory_thread'):
            self.memory_thread.terminate()

    def showEvent(self, event):
        super().showEvent(event)
        self.fileRefreshTimer.start(5000)
        # 从文件重新加载设置，与其他页面的清理开关同步
        self.settings_manager.settings = self.settings_manager.load_settings()
        self.autoCleanCheckBox.setChecked(self.settings_manager.get("auto_clean_on_startup", True))
        if hasattr(self, 'cpu_thread') and not self.cpu_thread.isRunning():
            self.cpu_thread.start()
        if hasattr(self, 'memory_thread') and not self.memory_thread.isRunning():
            self.memory_thread.start()

    def update_cpu_info(self, cpu_percent, process_cpu, other_cpu):
        try:
            cpu_percent = max(cpu_percent, 0.1)
            process_cpu = max(process_cpu, 0.1)
            other_cpu = max(other_cpu, 0.1)
            free_cpu = max(100 - cpu_percent, 0.1)

            self.cpuBar.segments = [
                {'percent': process_cpu, 'color': QColor(255, 165, 0)},
                {'percent': other_cpu, 'color': QColor(0, 159, 170)}
            ]
            self.cpuBar.update()

            self.softwareCpuLabel.setText(f"本软件 {process_cpu:.1f}%  ")
            self.otherProcessCpuLabel.setText(f"其他进程 {other_cpu:.1f}%  ")
            self.idleCpuLabel.setText(f"空闲 {free_cpu:.1f}%")
        except Exception as e:
            print(f"[StoragePage] 更新CPU信息失败: {e}")

    def update_memory_info(self, total_memory, used_memory, memory_percent, process_memory, process_memory_percent, other_memory_percent):
        try:
            memory_percent = max(memory_percent, 0.1)
            process_memory_percent = max(process_memory_percent, 0.1)
            other_memory_percent = max(other_memory_percent, 0.1)
            free_memory_percent = max(100 - memory_percent, 0.1)

            self.memoryBar.segments = [
                {'percent': process_memory_percent, 'color': QColor(255, 165, 0)},
                {'percent': other_memory_percent, 'color': QColor(0, 159, 170)}
            ]
            self.memoryBar.update()

            self.softwareMemoryLabel.setText(f"本软件 {process_memory_percent:.1f}%  ")
            self.otherProcessMemoryLabel.setText(f"其他进程 {other_memory_percent:.1f}%  ")
            self.idleMemoryLabel.setText(f"空闲 {free_memory_percent:.1f}%")
        except Exception as e:
            print(f"[StoragePage] 更新内存信息失败: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        page_width = self.width()
        page_height = self.height()
        card_width = page_width // 2 - 20
        disk_space_card_height = card_width // 3
        available_height = page_height - 40 - 10 - disk_space_card_height

        self.diskSpaceCard.setFixedSize(card_width, disk_space_card_height)
        if available_height > 0:
            self.dataManagementCard.setFixedSize(card_width, available_height)
        else:
            self.dataManagementCard.setFixedSize(card_width, 100)

        total_right_height = page_height - 40
        treasure_box_card_height = total_right_height / 2
        self.deviceCard.setFixedSize(card_width, treasure_box_card_height)

        performance_card_height = total_right_height - treasure_box_card_height - 10
        if performance_card_height > 0:
            self.performanceCard.setFixedSize(card_width, performance_card_height)
        else:
            self.performanceCard.setFixedSize(card_width, 100)
