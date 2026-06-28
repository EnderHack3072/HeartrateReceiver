import base64
from io import BytesIO
from PyQt6.QtGui import QIcon, QPixmap


def get_icon_from_base64(base64_data):
    """从base64编码数据创建QIcon"""
    try:
        icon_data = base64.b64decode(base64_data)
        icon_stream = BytesIO(icon_data)
        pixmap = QPixmap()
        pixmap.loadFromData(icon_stream.getvalue())
        return QIcon(pixmap)
    except Exception as e:
        print(f"Error creating icon from base64: {e}")
        return QIcon()
