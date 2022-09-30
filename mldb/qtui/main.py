import sys

from PySide6.QtWidgets import QApplication

from .app import MainWindow


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
