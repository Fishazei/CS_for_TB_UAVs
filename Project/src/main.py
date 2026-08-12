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
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def handle_config_applied(config_str: str):
  """Функция-слот для обработки применения конфигурации."""
  print("\n=== [Backend] Сигнал о применении конфига получен ===")
  print(f"Длина строки конфигурации: {len(config_str)} символов")
  # Здесь в будущем будет парсинг YAML и инициализация классов моторов и физики


def main():
  app = QApplication(sys.argv)

  window = MainWindow()

  window.show()
  sys.exit(app.exec())


if __name__ == "__main__":
  main()
