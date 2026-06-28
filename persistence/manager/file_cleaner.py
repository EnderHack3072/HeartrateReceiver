import os


class FileCleaner:
    @staticmethod
    def clean_small_files(data_dir, size_threshold=5 * 1024, skip_latest=True):
        """清理data_dir下小于阈值的小文件，返回清理数量"""
        if not os.path.exists(data_dir) or not os.path.isdir(data_dir):
            return 0
        try:
            files = os.listdir(data_dir)
            cleaned_count = 0
            latest_file = None
            if skip_latest and files:
                sorted_files = sorted(files, reverse=True)
                latest_file = sorted_files[0]
            for file in files:
                if skip_latest and file == latest_file:
                    continue
                file_path = os.path.join(data_dir, file)
                if os.path.isfile(file_path):
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size < size_threshold:
                            os.remove(file_path)
                            cleaned_count += 1
                    except Exception:
                        pass
            return cleaned_count
        except Exception as e:
            print(f"[FileCleaner] 清理失败: {e}")
            return 0
