from PySide6 import QtWidgets


class StatusDisplay:

    def __init__(self, parent: QtWidgets.QMainWindow):
        self.parent = parent
        self.status_bar = parent.statusBar()
        self.progress_bar = QtWidgets.QProgressBar()
        self.mbox = None

        self.status_bar.insertPermanentWidget(0, self.progress_bar)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)

    def start_progress_bar(self, max_v=100):
        self.progress_bar.setMaximum(max_v)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

    def end_progress_bar(self):
        self.progress_bar.setVisible(False)

    def set_progress(self, p: int):
        if p >= self.progress_bar.maximum():
            self.progress_bar.setVisible(False)
        else:
            self.progress_bar.setVisible(True)
        self.progress_bar.setValue(p)

    def update_progress_bar(self, n=1, with_message: str = None):
        v = self.progress_bar.value() + n
        self.progress_bar.setValue(v)
        if v >= self.progress_bar.maximum():
            self.end_progress_bar()

        if with_message:
            self.show_message(with_message)

    def show_message(self, message: str, timeout=5000):
        self.status_bar.showMessage(message, timeout)

    def show_error_message(self, error_message: str):
        QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning,
            'Error',
            error_message,
            parent=self.parent
        ).show()
