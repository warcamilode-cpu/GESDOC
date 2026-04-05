"""
main.py - Entry point for DocManager
Run with: python main.py
"""
import sys
import os

# Ensure current directory is in path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFont

import database as db


def main():
    # ── MUST be set BEFORE QApplication is created ────────────────────────────
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Required for QWebEngineView on Windows (shared OpenGL contexts)
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    app = QApplication(sys.argv)
    app.setApplicationName("DocManager")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")

    font = QFont("Times New Roman", 14)
    app.setFont(font)

    # Initialize database
    db.init_db()
    db.init_folders()
    db.migrate_existing_to_vault()  # copy any external docs into vault
    db.add_author_column()           # add author column if missing

    # Apply dark theme
    from utils.theme import apply_theme
    apply_theme(app, dark=True)

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
