from PySide6.QtWidgets import QWidget


class BaseExpView(QWidget):

    def __init__(self, expid: str):
        super().__init__()
        self.expid = expid

    def refresh(self):
        raise NotImplementedError
