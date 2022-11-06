from PySide6.QtWidgets import (
    QDialog, QWidget, QHBoxLayout,
    QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLineEdit, QLabel
)

from mldb import Database

from .db_iop import DBMethod


class GroupEditDialog(QDialog):

    def __init__(self, parent: QWidget, expids: str):
        super().__init__(parent)

        self.expid = expids[0]  # TODO: support multiple exps at once

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel(self.expid))

        hb = QWidget()
        hb.layout = QHBoxLayout(hb)
        self.txt_new_group = QLineEdit()
        hb.layout.addWidget(self.txt_new_group)
        self.btn_new_group = QPushButton('+')
        self.btn_new_group.clicked.connect(self.add_group)
        hb.layout.addWidget(self.btn_new_group)
        self.btn_rem_group = QPushButton('-')
        self.btn_rem_group.clicked.connect(self.rem_group)
        hb.layout.addWidget(self.btn_rem_group)

        self.layout.addWidget(hb)

        self.group_list = QListWidget()
        self.layout.addWidget(self.group_list)

        self.refresh_group_list()

    def refresh_group_list(self, *_, **__):
        DBMethod(lambda db, e: db.get_groups_of_exp(e), self.expid, slot=self.groups_returned).start()

    def groups_returned(self, groups):
        self.group_list.clear()
        for group in groups:
            self.group_list.addItem(QListWidgetItem(group))

    def add_group(self):
        group = self.txt_new_group.text()
        DBMethod(lambda db, e, g: db.add_to_group(e, g), self.expid, group, slot=self.refresh_group_list).start()

    def rem_group(self):
        selection = self.group_list.currentItem().text()
        print(selection)
        # DBMethod(lambda db, g: db.remove_from_group(e, g), self.expid, selection, slot=self.refresh_group_list)
