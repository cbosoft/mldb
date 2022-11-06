from PySide6.QtWidgets import QWidget


class BaseExpView(QWidget):

    def __init__(self, *expids: str):
        super().__init__()
        self.expids = expids

    def refresh(self):
        raise NotImplementedError
