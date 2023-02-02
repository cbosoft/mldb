from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class FuncRunner(QRunnable):
    def __init__(self, f, *args):
        super().__init__()
        self.f = f
        self.args = args

    def run(self):
        self.f(*self.args)

    def start(self):
        QThreadPool.globalInstance().start(self)
