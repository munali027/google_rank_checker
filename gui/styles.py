# Qt QSS Design System for Google Keyword Rank Checker

DARK_THEME_QSS = """
QMainWindow {
    background-color: #181825;
    color: #CDD6F4;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

QWidget {
    color: #CDD6F4;
    font-family: "Segoe UI", sans-serif;
}

QGroupBox {
    background-color: #1E1E2E;
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: bold;
    color: #89B4FA;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #181825;
}

QLabel {
    color: #CDD6F4;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #313244;
    border: 1px solid #45475A;
    border-radius: 6px;
    padding: 6px 10px;
    color: #F5E0DC;
    selection-background-color: #585B70;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #89B4FA;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QPushButton {
    background-color: #45475A;
    border: 1px solid #585B70;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    color: #CDD6F4;
}

QPushButton:hover {
    background-color: #585B70;
    border-color: #89B4FA;
}

QPushButton:disabled {
    background-color: #1E1E2E;
    border-color: #313244;
    color: #6C7086;
}

QPushButton#btnStart {
    background-color: #A6E3A1;
    color: #11111B;
    border: none;
}

QPushButton#btnStart:hover {
    background-color: #94E2D5;
}

QPushButton#btnPause {
    background-color: #F9E2AF;
    color: #11111B;
    border: none;
}

QPushButton#btnPause:hover {
    background-color: #FAB387;
}

QPushButton#btnResume {
    background-color: #89B4FA;
    color: #11111B;
    border: none;
}

QPushButton#btnResume:hover {
    background-color: #74C7EC;
}

QPushButton#btnStop {
    background-color: #F38BA8;
    color: #11111B;
    border: none;
}

QPushButton#btnStop:hover {
    background-color: #E78284;
}

QPushButton#btnClearSession {
    background-color: #E78284;
    color: #11111B;
    border: none;
}

QPushButton#btnClearSession:hover {
    background-color: #EA999C;
}

QProgressBar {
    border: 1px solid #313244;
    border-radius: 6px;
    text-align: center;
    background-color: #1E1E2E;
    color: #F5E0DC;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #89B4FA;
    border-radius: 5px;
}

QTableWidget {
    background-color: #1E1E2E;
    border: 1px solid #313244;
    border-radius: 8px;
    gridline-color: #313244;
    selection-background-color: #45475A;
}

QHeaderView::section {
    background-color: #181825;
    color: #89B4FA;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #313244;
    padding: 6px;
}

QTextEdit {
    background-color: #11111B;
    border: 1px solid #313244;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    color: #A6ADC8;
}

/* Metric Cards */
QWidget#metricCard {
    background-color: #1E1E2E;
    border: 1px solid #313244;
    border-radius: 8px;
}

QLabel#metricTitle {
    color: #A6ADC8;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
}

QLabel#metricValue {
    color: #89B4FA;
    font-size: 20px;
    font-weight: bold;
}

/* Captcha Alert Banner */
QWidget#captchaBanner {
    background-color: #F38BA8;
    border-radius: 8px;
    padding: 8px;
}

QLabel#captchaText {
    color: #11111B;
    font-size: 14px;
    font-weight: bold;
}

/* Footer Credit Label */
QLabel#lblCredit {
    color: #CBA6F7;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
    background-color: #1E1E2E;
    border: 1px solid #313244;
    border-radius: 6px;
}
"""
