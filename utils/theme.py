"""
utils/theme.py - Dark and Light themes for DocManager
"""

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}
QMenuBar::item:selected { background-color: #313244; }
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
}
QMenu::item:selected { background-color: #45475a; }

QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    spacing: 4px;
    padding: 4px;
}
QToolButton {
    background-color: transparent;
    color: #cdd6f4;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
}
QToolButton:hover { background-color: #313244; }
QToolButton:pressed { background-color: #45475a; }

QSplitter::handle { background-color: #313244; width: 2px; height: 2px; }

QScrollBar:vertical {
    background: #181825; width: 10px; border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #45475a; border-radius: 5px; min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QScrollBar:horizontal {
    background: #181825; height: 10px; border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #45475a; border-radius: 5px; min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #585b70; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

QTabWidget::pane { border: 1px solid #313244; background-color: #1e1e2e; }
QTabBar::tab {
    background-color: #181825; color: #6c7086;
    padding: 6px 14px; border: 1px solid #313244;
    border-bottom: none; border-radius: 4px 4px 0 0;
}
QTabBar::tab:selected { background-color: #1e1e2e; color: #cdd6f4; border-bottom: 2px solid #89b4fa; }
QTabBar::tab:hover:!selected { background-color: #313244; color: #cdd6f4; }

QListWidget {
    background-color: #181825; color: #cdd6f4;
    border: 1px solid #313244; border-radius: 6px;
    outline: none;
}
QListWidget::item { padding: 6px 8px; border-radius: 4px; }
QListWidget::item:selected { background-color: #313244; color: #89b4fa; }
QListWidget::item:hover:!selected { background-color: #25253a; }

QTreeWidget {
    background-color: #181825; color: #cdd6f4;
    border: 1px solid #313244; border-radius: 6px; outline: none;
}
QTreeWidget::item { padding: 4px 6px; }
QTreeWidget::item:selected { background-color: #313244; color: #89b4fa; }
QHeaderView::section {
    background-color: #1e1e2e; color: #6c7086;
    padding: 6px; border: none; border-bottom: 1px solid #313244;
}

QPushButton {
    background-color: #313244; color: #cdd6f4;
    border: none; border-radius: 6px;
    padding: 6px 14px; font-weight: 500;
}
QPushButton:hover { background-color: #45475a; }
QPushButton:pressed { background-color: #585b70; }
QPushButton#primaryBtn {
    background-color: #89b4fa; color: #1e1e2e; font-weight: 600;
}
QPushButton#primaryBtn:hover { background-color: #b4d0ff; }
QPushButton#dangerBtn { background-color: #f38ba8; color: #1e1e2e; }
QPushButton#dangerBtn:hover { background-color: #f5a3b5; }
QPushButton#successBtn { background-color: #a6e3a1; color: #1e1e2e; }

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #313244; color: #cdd6f4;
    border: 1px solid #45475a; border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #89b4fa; selection-color: #1e1e2e;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #89b4fa;
}

QComboBox {
    background-color: #313244; color: #cdd6f4;
    border: 1px solid #45475a; border-radius: 6px;
    padding: 5px 10px;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { image: none; border: none; }
QComboBox QAbstractItemView {
    background-color: #313244; color: #cdd6f4;
    selection-background-color: #45475a; border: 1px solid #45475a;
}

QLabel { color: #cdd6f4; }
QLabel#sectionTitle { color: #89b4fa; font-weight: 600; font-size: 14px; }
QLabel#subtitle { color: #6c7086; font-size: 11px; }

QStatusBar { background-color: #181825; color: #6c7086; border-top: 1px solid #313244; }

QGroupBox {
    color: #6c7086; border: 1px solid #313244;
    border-radius: 6px; margin-top: 12px; padding-top: 8px;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #89b4fa; }

QFrame#commentCard {
    background-color: #181825; border: 1px solid #313244;
    border-radius: 8px; padding: 8px;
}
QFrame#commentCard:hover { border-color: #45475a; }
QFrame#highlightBar {
    background-color: #f9e2af; border-radius: 4px;
    padding: 4px 8px; color: #1e1e2e; font-style: italic;
}

QSlider::groove:horizontal {
    background: #313244; height: 4px; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #89b4fa; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}

QProgressBar {
    background-color: #313244; border: none; border-radius: 4px; height: 6px;
}
QProgressBar::chunk { background-color: #89b4fa; border-radius: 4px; }

QDialog { background-color: #1e1e2e; }
QMessageBox { background-color: #1e1e2e; }

QCheckBox { color: #cdd6f4; spacing: 6px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border: 1px solid #45475a;
    border-radius: 3px; background-color: #313244;
}
QCheckBox::indicator:checked { background-color: #89b4fa; border-color: #89b4fa; }
"""


LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #eff1f5;
    color: #4c4f69;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QMenuBar {
    background-color: #e6e9ef;
    color: #4c4f69;
    border-bottom: 1px solid #ccd0da;
}
QMenuBar::item:selected { background-color: #ccd0da; }
QMenu {
    background-color: #eff1f5;
    color: #4c4f69;
    border: 1px solid #ccd0da;
}
QMenu::item:selected { background-color: #ccd0da; }

QToolBar {
    background-color: #e6e9ef;
    border-bottom: 1px solid #ccd0da;
    spacing: 4px; padding: 4px;
}
QToolButton {
    background-color: transparent; color: #4c4f69;
    border: none; border-radius: 4px; padding: 4px 8px;
}
QToolButton:hover { background-color: #ccd0da; }
QToolButton:pressed { background-color: #bcc0cc; }

QSplitter::handle { background-color: #ccd0da; width: 2px; height: 2px; }

QScrollBar:vertical { background: #e6e9ef; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #bcc0cc; border-radius: 5px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: #acb0be; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background: #e6e9ef; height: 10px; border-radius: 5px; }
QScrollBar::handle:horizontal { background: #bcc0cc; border-radius: 5px; min-width: 20px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

QTabWidget::pane { border: 1px solid #ccd0da; background-color: #eff1f5; }
QTabBar::tab {
    background-color: #e6e9ef; color: #8c8fa1;
    padding: 6px 14px; border: 1px solid #ccd0da;
    border-bottom: none; border-radius: 4px 4px 0 0;
}
QTabBar::tab:selected { background-color: #eff1f5; color: #4c4f69; border-bottom: 2px solid #1e66f5; }
QTabBar::tab:hover:!selected { background-color: #ccd0da; color: #4c4f69; }

QListWidget {
    background-color: #e6e9ef; color: #4c4f69;
    border: 1px solid #ccd0da; border-radius: 6px; outline: none;
}
QListWidget::item { padding: 6px 8px; border-radius: 4px; }
QListWidget::item:selected { background-color: #ccd0da; color: #1e66f5; }
QListWidget::item:hover:!selected { background-color: #dce0e8; }

QTreeWidget {
    background-color: #e6e9ef; color: #4c4f69;
    border: 1px solid #ccd0da; border-radius: 6px; outline: none;
}
QTreeWidget::item { padding: 4px 6px; }
QTreeWidget::item:selected { background-color: #ccd0da; color: #1e66f5; }
QHeaderView::section {
    background-color: #eff1f5; color: #8c8fa1;
    padding: 6px; border: none; border-bottom: 1px solid #ccd0da;
}

QPushButton {
    background-color: #ccd0da; color: #4c4f69;
    border: none; border-radius: 6px;
    padding: 6px 14px; font-weight: 500;
}
QPushButton:hover { background-color: #bcc0cc; }
QPushButton:pressed { background-color: #acb0be; }
QPushButton#primaryBtn {
    background-color: #1e66f5; color: #ffffff; font-weight: 600;
}
QPushButton#primaryBtn:hover { background-color: #3d7ef7; }
QPushButton#dangerBtn { background-color: #d20f39; color: #ffffff; }
QPushButton#dangerBtn:hover { background-color: #e62957; }
QPushButton#successBtn { background-color: #40a02b; color: #ffffff; }

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff; color: #4c4f69;
    border: 1px solid #ccd0da; border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #1e66f5; selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #1e66f5;
}

QComboBox {
    background-color: #ffffff; color: #4c4f69;
    border: 1px solid #ccd0da; border-radius: 6px; padding: 5px 10px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff; color: #4c4f69;
    selection-background-color: #ccd0da;
}

QLabel { color: #4c4f69; }
QLabel#sectionTitle { color: #1e66f5; font-weight: 600; font-size: 14px; }
QLabel#subtitle { color: #8c8fa1; font-size: 11px; }

QStatusBar { background-color: #e6e9ef; color: #8c8fa1; border-top: 1px solid #ccd0da; }

QGroupBox {
    color: #8c8fa1; border: 1px solid #ccd0da;
    border-radius: 6px; margin-top: 12px; padding-top: 8px;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #1e66f5; }

QFrame#commentCard {
    background-color: #e6e9ef; border: 1px solid #ccd0da;
    border-radius: 8px; padding: 8px;
}
QFrame#commentCard:hover { border-color: #bcc0cc; }
QFrame#highlightBar {
    background-color: #faf4e1; border-left: 3px solid #df8e1d;
    border-radius: 4px; padding: 4px 8px; color: #4c4f69; font-style: italic;
}

QDialog { background-color: #eff1f5; }
QCheckBox { color: #4c4f69; spacing: 6px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border: 1px solid #ccd0da;
    border-radius: 3px; background-color: #ffffff;
}
QCheckBox::indicator:checked { background-color: #1e66f5; border-color: #1e66f5; }
"""


def apply_theme(app, dark=True):
    app.setStyleSheet(DARK_THEME if dark else LIGHT_THEME)


PRIORITY_COLORS_DARK = {
    "Alta": "#f38ba8",
    "Media": "#f9e2af",
    "Baja": "#a6e3a1",
}
PRIORITY_COLORS_LIGHT = {
    "Alta": "#d20f39",
    "Media": "#df8e1d",
    "Baja": "#40a02b",
}
STATUS_COLORS_DARK = {
    "Abierto": "#89b4fa",
    "Resuelto": "#a6e3a1",
    "Pendiente": "#fab387",
}
STATUS_COLORS_LIGHT = {
    "Abierto": "#1e66f5",
    "Resuelto": "#40a02b",
    "Pendiente": "#fe640b",
}
CATEGORY_ICONS = {
    "General": "💬",
    "Importante": "⭐",
    "Pregunta": "❓",
    "Corrección": "✏️",
    "Referencia": "🔗",
    "Tarea": "✅",
}
DOC_STATUS_COLORS = {
    "Por revisar": "#89b4fa",
    "En progreso": "#fab387",
    "Revisado": "#f9e2af",
    "Aprobado": "#a6e3a1",
}
