import os
import shutil
import subprocess


class StorageService:
    """存储服务 - 负责磁盘空间、文件列表等管理"""
    
    def __init__(self, signals):
        self.signals = signals
    
    def get_project_root(self):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def get_data_dir(self):
        return os.path.join(self.get_project_root(), 'data')
    
    def get_disk_space_info(self):
        try:
            app_path = self.get_project_root()
            total, used, free = shutil.disk_usage(app_path)
            total_gb = round(total / (1024 ** 3), 1)
            used_gb = round(used / (1024 ** 3), 1)
            used_percent = round(used / total * 100, 1) if total > 0 else 0
            return total_gb, used_gb, used_percent
        except Exception as e:
            print(f"[StorageService] 获取磁盘空间失败: {e}")
            return 0, 0, 0
    
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
    
    def get_app_size_info(self, total_gb):
        try:
            app_path = self.get_project_root()
            app_size = self._get_dir_size(app_path)
            app_size_gb = round(app_size / (1024 ** 3), 3)
            app_percent = round(app_size_gb / total_gb * 100, 1) if total_gb > 0 else 0
            return app_size_gb, app_percent
        except Exception as e:
            print(f"[StorageService] 获取软件大小失败: {e}")
            return 0, 0
    
    def get_file_list(self):
        data_dir = self.get_data_dir()
        
        if not os.path.exists(data_dir) or not os.path.isdir(data_dir):
            return [], 0, "", 0
            
        files = os.listdir(data_dir)
        
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
        
        return files, file_count, size_str, small_files_count
    
    def refresh_file_list(self):
        files, file_count, size_str, small_files_count = self.get_file_list()
        self.signals.file_list_updated.emit(files, file_count, size_str, small_files_count)
    
    def clean_small_files(self):
        data_dir = self.get_data_dir()
        
        if not os.path.exists(data_dir) or not os.path.isdir(data_dir):
            return
        
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
        return cleaned_count
    
    def open_data_directory(self):
        """打开数据目录"""
        data_dir = self.get_data_dir()
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        subprocess.Popen(['explorer', data_dir])
    
    def emit_disk_space_info(self):
        total_gb, used_gb, used_percent = self.get_disk_space_info()
        self.signals.disk_space_updated.emit(total_gb, used_gb, used_percent)
