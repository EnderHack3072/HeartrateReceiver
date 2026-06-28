import mmap
import struct
import os
import time


class MemoryShareManager:
    """内存共享管理器，用于在进程间共享心率数据"""
    
    # 共享内存区域的名称
    SHARED_MEM_NAME = "HeartRateSharedMemory"
    # 共享内存的大小（字节）
    SHARED_MEM_SIZE = 4096
    # 心率数据的结构体格式（BPM: int, timestamp: float）
    DATA_FORMAT = "if"
    # 数据大小
    DATA_SIZE = struct.calcsize(DATA_FORMAT)
    
    def __init__(self):
        self.shared_memory = None
        self.mmap_obj = None
        self.is_initialized = False
    
    def initialize(self):
        """初始化共享内存"""
        try:
            # 创建或打开共享内存区域
            self.shared_memory = mmap.mmap(
                -1,  # 使用匿名映射，或者指定文件描述符
                self.SHARED_MEM_SIZE,
                self.SHARED_MEM_NAME,
                mmap.ACCESS_WRITE
            )
            self.is_initialized = True
            print(f"[MemoryShare] 共享内存已创建: {self.SHARED_MEM_NAME}")
        except Exception as e:
            print(f"[MemoryShare] 初始化共享内存失败: {e}")
            self.is_initialized = False
    
    def update_heart_rate(self, heart_rate):
        """更新共享内存中的心率数据"""
        if not self.is_initialized:
            return
        
        try:
            # 获取当前时间戳
            timestamp = time.time()
            
            # 打包数据
            data = struct.pack(self.DATA_FORMAT, heart_rate, timestamp)
            
            # 写入共享内存
            self.shared_memory.seek(0)
            self.shared_memory.write(data)
            self.shared_memory.flush()
            
        except Exception as e:
            print(f"[MemoryShare] 更新心率数据失败: {e}")
    
    def close(self):
        """关闭共享内存"""
        if self.shared_memory:
            try:
                self.shared_memory.close()
                print(f"[MemoryShare] 共享内存已关闭: {self.SHARED_MEM_NAME}")
            except Exception as e:
                print(f"[MemoryShare] 关闭共享内存失败: {e}")
            finally:
                self.shared_memory = None
                self.is_initialized = False
    
    def __del__(self):
        """析构函数，确保共享内存被关闭"""
        self.close()


# 用于外部程序读取共享内存的辅助函数
def read_heart_rate_from_memory():
    """从共享内存中读取心率数据
    
    Returns:
        tuple: (heart_rate, timestamp) 或 None
    """
    try:
        with mmap.mmap(
            -1,
            MemoryShareManager.SHARED_MEM_SIZE,
            MemoryShareManager.SHARED_MEM_NAME,
            mmap.ACCESS_READ
        ) as shared_memory:
            shared_memory.seek(0)
            data = shared_memory.read(MemoryShareManager.DATA_SIZE)
            if len(data) == MemoryShareManager.DATA_SIZE:
                return struct.unpack(MemoryShareManager.DATA_FORMAT, data)
            return None
    except Exception as e:
        print(f"[MemoryShare] 读取心率数据失败: {e}")
        return None
