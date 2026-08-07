import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from PyQt5.QtCore import QObject, pyqtSignal


class LogSignal(QObject):
    """Сигнал для передачи логов в UI"""
    new_log = pyqtSignal(str, str)  # level, message


class QtHandler(logging.Handler):
    """Обработчик логов, перенаправляющий в Qt сигнал"""

    def __init__(self):
        super().__init__()
        self.signal = LogSignal()
        self.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s',
                                            datefmt='%H:%M:%S'))

    def emit(self, record):
        msg = self.format(record)
        self.signal.new_log.emit(record.levelname, msg)


def setup_logger():
    """Настройка системы логирования"""
    logger = logging.getLogger('MotorStand')
    logger.setLevel(logging.DEBUG)

    # Qt обработчик для UI
    qt_handler = QtHandler()
    logger.addHandler(qt_handler)

    # Файловый обработчик
    file_handler = RotatingFileHandler(
        f'logs/motor_stand_{datetime.now():%Y%m%d_%H%M%S}.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))
    logger.addHandler(file_handler)

    return logger, qt_handler.signal