from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QComboBox, QLabel
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QTextCursor, QColor, QFont
from datetime import datetime


class LogConsole(QWidget):
    """Консоль для отображения логов"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Панель управления
        control_panel = QHBoxLayout()

        control_panel.addWidget(QLabel("Уровень:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_combo.setCurrentText("INFO")
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        control_panel.addWidget(self.level_combo)

        control_panel.addStretch()

        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self.clear_logs)
        control_panel.addWidget(self.clear_button)

        self.auto_scroll = QPushButton("Автоскролл: ВКЛ")
        self.auto_scroll.setCheckable(True)
        self.auto_scroll.setChecked(True)
        self.auto_scroll.clicked.connect(self.toggle_auto_scroll)
        control_panel.addWidget(self.auto_scroll)

        layout.addLayout(control_panel)

        # Текстовая область для логов
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.log_text)

        # Хранилище всех логов для фильтрации
        self.all_logs = []

    @pyqtSlot(str, str)
    def append_log(self, level: str, message: str):
        """Добавить лог в консоль"""
        # Сохраняем лог
        log_entry = {'level': level, 'message': message,
                     'timestamp': datetime.now()}
        self.all_logs.append(log_entry)

        # Проверяем фильтр
        if self.should_display(level):
            self.display_log(level, message)

    def display_log(self, level: str, message: str):
        """Отобразить лог с цветовым форматированием"""
        # Определяем цвет для уровня
        colors = {
            'DEBUG': '#888888',
            'INFO': '#4ecdc4',
            'WARNING': '#f9ca24',
            'ERROR': '#ff6b6b',
            'CRITICAL': '#ff0000'
        }

        color = colors.get(level, '#d4d4d4')

        # Форматируем сообщение
        formatted_msg = f'<span style="color: {color}; font-weight: bold;">[{level}]</span> '
        formatted_msg += f'<span style="color: #d4d4d4;">{message}</span>'

        # Добавляем в консоль
        self.log_text.append(formatted_msg)

        # Автоскролл
        if self.auto_scroll.isChecked():
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)

    def should_display(self, level: str) -> bool:
        """Проверить, нужно ли отображать лог данного уровня"""
        levels = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
        current_level = levels.get(self.level_combo.currentText(), 1)
        log_level = levels.get(level, 0)
        return log_level >= current_level

    def filter_logs(self):
        """Применить фильтр по уровню"""
        self.log_text.clear()
        for log in self.all_logs:
            if self.should_display(log['level']):
                self.display_log(log['level'], log['message'])

    def clear_logs(self):
        """Очистить консоль"""
        self.log_text.clear()
        self.all_logs.clear()

    def toggle_auto_scroll(self, checked):
        """Переключить автоскролл"""
        self.auto_scroll.setText(f"Автоскролл: {'ВКЛ' if checked else 'ВЫКЛ'}")