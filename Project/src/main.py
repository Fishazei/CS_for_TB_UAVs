# pySerial-3.5 for bluetooth
# pyyaml- for configs
# Логика следующая: настройка программы (при исп. StandConfig) -> запуск сценария (при исп. Scenario) -> сценарист -> переводчик команд (при исп. ModelConfig)
# -> Логические моторы -> Модуль управления ~> bluetooth ~> ардуино -> ESC

# HIL петля
"""
Формируем набор манёвров (сценарии)
На пк считаем физику для датчиков
Далее формируем MAVLink сигналы и отправляем их на ПолКонтр
Он считает изменения моторов и шлёт нам, мы пересчитываем
17 стих 
"""
# main.py
"""
import yaml
from src.core.scenario_manager import ScenarioManager
from src.core.command_interpreter import CommandInterpreter
from src.core.transition_engine import TransitionEngine, TransitionType
from src.models.virtual_motor import VirtualMotor
from src.models.command import Command, CommandType
from src.io.arduino_bridge import ArduinoBridge
import numpy as np

class TestController:
    def __init__(self, stand_config_path: str, model_config_path: str):
        # Загружаем конфиги
        with open(stand_config_path) as f:
            self.stand_config = yaml.safe_load(f)
        with open(model_config_path) as f:
            self.model_config = yaml.safe_load(f)

        # Создаем виртуальные моторы
        self.motors = {}
        for motor_config in self.stand_config['motors']:
            motor = VirtualMotor(motor_config['id'], motor_config)
            self.motors[motor_config['id']] = motor

        # Создаем компоненты
        self.interpreter = CommandInterpreter(self.model_config)
        self.transition_engine = TransitionEngine(
            self.stand_config['stand']['update_rate_hz']
        )
        self.scenario_manager = ScenarioManager(
            self.motors, self.interpreter, self.transition_engine
        )
        self.arduino_bridge = ArduinoBridge(self.stand_config)

    def create_test_scenario(self):
        #Пример создания тестового сценария
        scenario = self.scenario_manager.create_scenario("hover_test")

        # Висение 2 секунды
        scenario.add_command(Command(
            type=CommandType.HOVER,
            duration_ms=2000,
            intensity=0.5
        ))

        # Подъем
        scenario.add_command(Command(
            type=CommandType.CLIMB,
            duration_ms=1000,
            intensity=0.3,
            transition_type="smooth",
            transition_duration_ms=200
        ))

        # Крен вправо
        scenario.add_command(Command(
            type=CommandType.ROLL_RIGHT,
            duration_ms=1500,
            intensity=0.2
        ))

        # Генерируем профили с разными типами переходов
        self.scenario_manager.generate_profiles(TransitionType.SMOOTH)

        # Открываем редактор
        modified_profiles = self.scenario_manager.edit_profiles()

        # Сохраняем сценарий
        self.scenario_manager.save_scenario("test_scenario.yaml")

    def run_scenario(self, scenario_name: str):
        #Запуск сценария на стенде
        self.scenario_manager.load_scenario(scenario_name)

        # Подключаемся к Arduino
        self.arduino_bridge.connect_all()

        # Получаем профили
        time_points = self.scenario_manager.current_scenario.time_points
        motor_profiles = {}
        for motor_id, states in self.scenario_manager.current_scenario.power_profiles.items():
            motor_profiles[motor_id] = np.array([s.power for s in states])

        # Запускаем воспроизведение
        self.arduino_bridge.stream_profile(
            time_points,
            motor_profiles,
            self.stand_config['stand']['update_rate_hz']
        )

        self.arduino_bridge.disconnect_all()


# Использование
if __name__ == "__main__":
    controller = TestController("C:\\Users\\fisha\\source\\repos\\Work2\\CS_for_TB_UAVs\\Project\\configs\\4motorsExample\\StandConfigExample.yaml",
                                "C:\\Users\\fisha\\source\\repos\\Work2\\CS_for_TB_UAVs\\Project\\configs\\4motorsExample\\ModelConfigExample.yaml")
    controller.create_test_scenario()
    controller.run_scenario("test_scenario.yaml")
"""
# main.py
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.ui.main_window import MainWindow
from src.ui.styles import STYLE_SHEET


def main():
    # Создаем директорию для логов
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Настройка приложения
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE_SHEET)

    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
