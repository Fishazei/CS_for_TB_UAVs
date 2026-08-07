from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QComboBox, QDoubleSpinBox, QSpinBox, QLabel,
                             QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from models.command import Command, CommandType


class CommandListWidget(QWidget):
    """Виджет для управления списком команд сценария"""

    commands_changed = pyqtSignal(list)  # Список команд
    command_selected = pyqtSignal(int)  # Индекс выбранной команды

    def __init__(self, parent=None):
        super().__init__(parent)
        self.commands = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title_label = QLabel("Команды сценария")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4a9eff;")
        layout.addWidget(title_label)

        # Таблица команд
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "№", "Тип", "Длительность (мс)", "Интенсивность", "Тип перехода"
        ])

        # Настройка колонок
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        layout.addWidget(self.table)

        # Панель добавления команд
        add_panel = QVBoxLayout()

        # Выпадающий список типов команд
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([cmd.value for cmd in CommandType])
        type_layout.addWidget(self.type_combo)
        add_panel.addLayout(type_layout)

        # Параметры команды
        params_layout = QHBoxLayout()

        params_layout.addWidget(QLabel("Длительность (мс):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(100, 10000)
        self.duration_spin.setValue(1000)
        self.duration_spin.setSingleStep(100)
        params_layout.addWidget(self.duration_spin)

        params_layout.addWidget(QLabel("Интенсивность:"))
        self.intensity_spin = QDoubleSpinBox()
        self.intensity_spin.setRange(0.0, 1.0)
        self.intensity_spin.setValue(0.5)
        self.intensity_spin.setSingleStep(0.05)
        self.intensity_spin.setDecimals(2)
        params_layout.addWidget(self.intensity_spin)

        add_panel.addLayout(params_layout)

        # Тип перехода
        transition_layout = QHBoxLayout()
        transition_layout.addWidget(QLabel("Переход:"))
        self.transition_combo = QComboBox()
        self.transition_combo.addItems(["smooth", "linear", "none"])
        transition_layout.addWidget(self.transition_combo)

        transition_layout.addWidget(QLabel("Длительность (мс):"))
        self.transition_duration_spin = QSpinBox()
        self.transition_duration_spin.setRange(0, 1000)
        self.transition_duration_spin.setValue(200)
        self.transition_duration_spin.setSingleStep(50)
        transition_layout.addWidget(self.transition_duration_spin)

        add_panel.addLayout(transition_layout)

        layout.addLayout(add_panel)

        # Кнопки управления
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_command)
        button_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Удалить")
        self.remove_button.setObjectName("dangerButton")
        self.remove_button.clicked.connect(self.remove_command)
        button_layout.addWidget(self.remove_button)

        self.move_up_button = QPushButton("▲")
        self.move_up_button.clicked.connect(self.move_up)
        button_layout.addWidget(self.move_up_button)

        self.move_down_button = QPushButton("▼")
        self.move_down_button.clicked.connect(self.move_down)
        button_layout.addWidget(self.move_down_button)

        layout.addLayout(button_layout)

    def add_command(self):
        """Добавить новую команду"""
        try:
            command = Command(
                type=CommandType(self.type_combo.currentText()),
                duration_ms=self.duration_spin.value(),
                intensity=self.intensity_spin.value(),
                transition_type=self.transition_combo.currentText(),
                transition_duration_ms=self.transition_duration_spin.value()
            )
            self.commands.append(command)
            self.update_table()
            self.commands_changed.emit(self.commands)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить команду: {str(e)}")

    def remove_command(self):
        """Удалить выбранную команду"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.commands.pop(current_row)
            self.update_table()
            self.commands_changed.emit(self.commands)

    def move_up(self):
        """Переместить команду вверх"""
        current_row = self.table.currentRow()
        if current_row > 0:
            self.commands[current_row], self.commands[current_row - 1] = \
                self.commands[current_row - 1], self.commands[current_row]
            self.update_table()
            self.table.selectRow(current_row - 1)
            self.commands_changed.emit(self.commands)

    def move_down(self):
        """Переместить команду вниз"""
        current_row = self.table.currentRow()
        if current_row < len(self.commands) - 1:
            self.commands[current_row], self.commands[current_row + 1] = \
                self.commands[current_row + 1], self.commands[current_row]
            self.update_table()
            self.table.selectRow(current_row + 1)
            self.commands_changed.emit(self.commands)

    def update_table(self):
        """Обновить таблицу команд"""
        self.table.setRowCount(len(self.commands))
        for i, cmd in enumerate(self.commands):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(cmd.type.value))
            self.table.setItem(i, 2, QTableWidgetItem(str(cmd.duration_ms)))
            self.table.setItem(i, 3, QTableWidgetItem(f"{cmd.intensity:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(cmd.transition_type))

    def on_selection_changed(self):
        """Обработчик изменения выделения"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.command_selected.emit(current_row)

    def set_commands(self, commands: list):
        """Установить список команд"""
        self.commands = commands.copy()
        self.update_table()

    def get_commands(self) -> list:
        """Получить список команд"""
        return self.commands.copy()