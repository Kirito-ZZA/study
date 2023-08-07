import typing
from PyQt5.QtCore import QObject, QSettings


class Settings(QObject):
    def __init__(self, file="", parent=None, logger=None):
        """ini配置文件读取类

        Args:
            file (str, optional): ini文件路径. Defaults to "".
            parent (QObject, optional): 父类窗口实例. Defaults to None.
            logger (Logger, optional): 日志实例. Defaults to None.
        """        
        super().__init__(parent)
        self.parent = parent
        self.logger = logger

        self.setting = QSettings(file, QSettings.IniFormat)
        self.setting.setIniCodec("utf-8")  # 可以支持中文

    def read(self, section, key, default_val, dtype):
        return self.setting.value(f"{section}/{key}", default_val, dtype)
    
    def write(self, section, key, value):
        self.setting.setValue(f"{section}/{key}", value)
