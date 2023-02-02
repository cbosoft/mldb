from typing import List

from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
)
from PySide6.QtCore import Signal

from mldb import Database

from .db_iop import DBMethod


class GroupEditDialog(QDialog):

    groups_changed = Signal()

    def __init__(self, parent: QWidget, expids: List[str]):
        super().__init__(parent)

        self.expids = expids  # TODO: support multiple exps at once
        self.groupset = None
        self.i = -1

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel(", ".join(self.expids)))

        hb = QWidget()
        hb.layout = QHBoxLayout(hb)
        self.txt_new_group = QLineEdit()
        hb.layout.addWidget(self.txt_new_group)
        self.btn_new_group = QPushButton("+")
        self.btn_new_group.clicked.connect(self.add_group)
        hb.layout.addWidget(self.btn_new_group)
        self.btn_rem_group = QPushButton("-")
        self.btn_rem_group.clicked.connect(self.rem_group)
        hb.layout.addWidget(self.btn_rem_group)

        self.layout.addWidget(hb)

        self.group_list = QListWidget()
        self.layout.addWidget(self.group_list)

        self.refresh_group_list()

    def refresh_group_list(self, *_, **__):
        self.groupset = None
        self.i = len(self.expids)
        for expid in self.expids:
            DBMethod(
                Database.get_groups_of_exp, (expid,), slot=self.groups_returned
            ).start()

    def groups_returned(self, groups):
        if self.groupset is None:
            self.groupset = set(groups)
        else:
            self.groupset = self.groupset.intersection(groups)

        self.i -= 1
        if self.i < 1:
            self.group_list.clear()
            for group in self.groupset:
                self.group_list.addItem(QListWidgetItem(group))
            self.groups_changed.emit()

    def add_group(self):
        group = self.txt_new_group.text()
        DBMethod(
            Database.add_to_group,
            *[(expid, group) for expid in self.expids],
            slot=self.refresh_group_list
        ).start()

    def rem_group(self):
        selected_group = self.group_list.currentItem().text()
        DBMethod(
            Database.remove_from_group,
            *[(expid, selected_group) for expid in self.expids],
            slot=self.refresh_group_list
        ).start()
