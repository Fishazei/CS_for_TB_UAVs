STYLE_SHEET = """
QMainWindow {
    background-color: #2b2b2b;
}

QTabWidget::pane {
    border: 1px solid #444;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background-color: #3c3c3c;
    color: #ccc;
    padding: 8px 16px;
    border: 1px solid #444;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #2b2b2b;
    color: #fff;
    border-bottom: 2px solid #4a9eff;
}

QGroupBox {
    color: #ccc;
    border: 1px solid #444;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 16px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QLabel {
    color: #ccc;
}

QPushButton {
    background-color: #4a9eff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #3a8eef;
}

QPushButton:pressed {
    background-color: #2a7edf;
}

QPushButton:disabled {
    background-color: #555;
    color: #888;
}

QPushButton#dangerButton {
    background-color: #ff4444;
}

QPushButton#dangerButton:hover {
    background-color: #ef3333;
}

QPushButton#successButton {
    background-color: #44bb44;
}

QPushButton#successButton:hover {
    background-color: #33aa33;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #3c3c3c;
    color: #ccc;
    border: 1px solid #555;
    padding: 4px;
    border-radius: 3px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #4a9eff;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: #4a4a4a;
    border-left: 1px solid #555;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #4a4a4a;
    border-left: 1px solid #555;
}

QTableWidget {
    background-color: #2b2b2b;
    color: #ccc;
    gridline-color: #444;
    border: 1px solid #444;
}

QTableWidget::item {
    padding: 4px;
}

QTableWidget::item:selected {
    background-color: #4a9eff;
}

QHeaderView::section {
    background-color: #3c3c3c;
    color: #ccc;
    padding: 4px;
    border: 1px solid #444;
}

QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #555;
    min-height: 20px;
    border-radius: 6px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QMenuBar {
    background-color: #2b2b2b;
    color: #ccc;
    border-bottom: 1px solid #444;
}

QMenuBar::item:selected {
    background-color: #4a9eff;
}

QMenu {
    background-color: #2b2b2b;
    color: #ccc;
    border: 1px solid #444;
}

QMenu::item:selected {
    background-color: #4a9eff;
}

QStatusBar {
    background-color: #2b2b2b;
    color: #ccc;
    border-top: 1px solid #444;
}

QSplitter::handle {
    background-color: #444;
}

QToolTip {
    background-color: #2b2b2b;
    color: #ccc;
    border: 1px solid #4a9eff;
    padding: 4px;
}
"""