# ui/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout,
                             QWidget, QStatusBar, QMessageBox, QMenuBar,
                             QAction, QMenu, QApplication)
from PyQt5.QtCore import Qt, pyqtSlot
import sys
import logging

from src.ui.config_tab import ConfigTab
from src.ui.scenario_tab import ScenarioTab
from src.ui.log_console import LogConsole
from src.utils.logger import setup_logger

logger = logging.getLogger('MotorStand')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()

        logger.info("Приложение запущено")

    def setup_logging(self):
        """Настройка логирования"""
        self.logger_instance, self.log_signal = setup_logger()

        # Подключаем сигнал к консоли
        self.log_signal.new_log.connect(self.append_log)

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Motor Stand Controller v2.0")
        self.setGeometry(100, 100, 1400, 900)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Вкладки
        self.tabs = QTabWidget()

        # Вкладка конфигурации
        self.config_tab = ConfigTab()
        self.config_tab.config_applied.connect(self.on_config_applied)
        self.config_tab.motors_count_changed.connect(self.on_motors_count_changed)
        self.tabs.addTab(self.config_tab, "⚙ Конфигурация")

        # Вкладка сценариев
        self.scenario_tab = ScenarioTab()
        self.tabs.addTab(self.scenario_tab, "📋 Сценарии")

        main_layout.addWidget(self.tabs, stretch=3)

        # Консоль логов
        self.log_console = LogConsole()
        main_layout.addWidget(self.log_console, stretch=1)

    def setup_menu(self):
        """Настройка меню"""
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("Файл")

        load_config_action = QAction("Загрузить конфиг", self)
        load_config_action.triggered.connect(self.config_tab.load_config)
        file_menu.addAction(load_config_action)

        save_config_action = QAction("Сохранить конфиг", self)
        save_config_action.triggered.connect(self.save_config)
        file_menu.addAction(save_config_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Сценарий
        scenario_menu = menubar.addMenu("Сценарий")

        new_scenario_action = QAction("Новый сценарий", self)
        scenario_menu.addAction(new_scenario_action)

        load_scenario_action = QAction("Загрузить сценарий", self)
        load_scenario_action.triggered.connect(self.scenario_tab.load_scenario)
        scenario_menu.addAction(load_scenario_action)

        save_scenario_action = QAction("Сохранить сценарий", self)
        save_scenario_action.triggered.connect(self.scenario_tab.save_scenario)
        scenario_menu.addAction(save_scenario_action)

        # Меню Вид
        view_menu = menubar.addMenu("Вид")

        clear_log_action = QAction("Очистить логи", self)
        clear_log_action.triggered.connect(self.log_console.clear_logs)
        view_menu.addAction(clear_log_action)

        # Меню Помощь
        help_menu = menubar.addMenu("Помощь")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        """Настройка строки состояния"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

    @pyqtSlot(str, str)
    def append_log(self, level: str, message: str):
        """Добавить лог в консоль"""
        self.log_console.append_log(level, message)

    @pyqtSlot(dict)
    def on_config_applied(self, config: dict):
        """Обработчик применения конфигурации"""
        motor_count = len(config.get('motors', []))
        self.scenario_tab.update_motor_graphs(motor_count)
        self.status_bar.showMessage(f"Конфигурация применена: {motor_count} моторов")

    @pyqtSlot(int)
    def on_motors_count_changed(self, count: int):
        """Обработчик изменения количества моторов"""
        self.scenario_tab.update_motor_graphs(count)

    def save_config(self):
        """Сохранить конфигурацию"""
        # Здесь можно реализовать сохранение текущего конфига
        logger.info("Сохранение конфигурации")

    def show_about(self):
        """Показать окно "О программе" """
        QMessageBox.about(self, "О программе",
                          "Motor Stand Controller v2.0\n\n"
                          "Система управления стендом имитации моторных групп дронов\n\n"
                          "© 2024"
                          )

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        reply = QMessageBox.question(
            self, 'Подтверждение выхода',
            'Вы уверены, что хотите выйти?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            logger.info("Приложение закрыто")
            event.accept()
        else:
            event.ignore()