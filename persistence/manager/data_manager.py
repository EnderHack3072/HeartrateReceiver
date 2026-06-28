import os
import csv
from datetime import datetime
import threading


class DataManager:
    def __init__(self, batch_size=50, max_points_per_file=1000):
        """
        初始化数据管理器

        Args:
            batch_size: 每多少个数据写一次文件，默认50
            max_points_per_file: 每个文件最大数据点数量，默认1000
        """
        self.batch_size = batch_size
        self.max_points_per_file = max_points_per_file
        self.data_buffer = []
        self.current_file_points = 0
        self.file_path = self._generate_file_path()
        self.lock = threading.Lock()
        self._ensure_directory()
        self._create_csv_file()

    def _get_project_root(self):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _generate_file_path(self):
        """
        生成数据文件路径

        Returns:
            str: 数据文件的绝对路径
        """
        data_dir = os.path.join(self._get_project_root(), "data")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"heart_rate_{timestamp}.hrof"
        return os.path.join(data_dir, filename)

    def _ensure_directory(self):
        """
        确保数据目录存在
        """
        data_dir = os.path.dirname(self.file_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

    def _create_csv_file(self):
        """
        创建CSV文件
        """
        try:
            with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"创建CSV文件出错: {e}")

    def collect_data(self, heart_rate):
        """
        收集心率数据

        Args:
            heart_rate: 心率值
        """
        if heart_rate == 0:
            return

        with self.lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            self.data_buffer.append([timestamp, heart_rate])

            if self.current_file_points + len(self.data_buffer) > self.max_points_per_file:
                remaining_points = self.max_points_per_file - self.current_file_points

                if remaining_points > 0:
                    data_to_write = self.data_buffer[:remaining_points]
                    self._write_data_to_file(data_to_write)
                    self.current_file_points += len(data_to_write)

                    self.data_buffer = self.data_buffer[remaining_points:]

                self._create_new_file()

            elif len(self.data_buffer) >= self.batch_size:
                self.write_data()

    def write_data(self):
        """
        将缓冲数据写入文件
        """
        if not self.data_buffer:
            return

        self._write_data_to_file(self.data_buffer)
        self.data_buffer = []

    def _write_data_to_file(self, data):
        """
        将数据写入当前文件

        Args:
            data: 要写入的数据
        """
        try:
            with open(self.file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(data)
                f.flush()
                os.fsync(f.fileno())

            self.current_file_points += len(data)
        except Exception as e:
            print(f"写入数据出错: {e}")

    def _create_new_file(self):
        """
        创建新的数据文件
        """
        self.file_path = self._generate_file_path()
        self.current_file_points = 0
        self._create_csv_file()
        print(f"创建新的数据文件: {self.file_path}")

    def flush_data(self):
        """
        确保所有数据写入磁盘
        """
        if self.data_buffer:
            self.write_data()

    def close(self):
        """
        关闭数据管理器，确保所有数据被写入
        """
        self.flush_data()
        print(f"数据已保存到: {self.file_path}")

    def clean_up_files(self):
        """
        整理数据文件，删除 <=10KB 的文件，只保留 >=10KB 的文件
        """
        data_dir = os.path.join(self._get_project_root(), "data")
        if not os.path.exists(data_dir):
            return {"deleted": 0, "kept": 0, "total": 0}

        deleted_count = 0
        kept_count = 0
        total_count = 0

        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)

            if os.path.isfile(file_path):
                total_count += 1
                file_size = os.path.getsize(file_path)

                if file_size <= 10 * 1024:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"[FileCleanup] 已删除文件: {filename} ({file_size} bytes)")
                    except Exception as e:
                        print(f"[FileCleanup] 删除文件失败 {filename}: {e}")
                else:
                    kept_count += 1
                    print(f"[FileCleanup] 保留文件: {filename} ({file_size} bytes)")

        result = {
            "deleted": deleted_count,
            "kept": kept_count,
            "total": total_count
        }
        print(f"[FileCleanup] 整理完成 - 总数: {total_count}, 删除: {deleted_count}, 保留: {kept_count}")
        return result
