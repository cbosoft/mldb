from typing import List, Union
import re

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QLineEdit,
    QHeaderView,
)
from PySide6.QtCore import Signal, Qt
import psycopg2.sql as sql

from .db_iop import DBQuery, DBMethod, Database
from .exp_compare_and_vew import ExpCompareAndViewDialog
from .edit_groups import GroupEditDialog


class ExperimentListWidget(QWidget):
    QUERIES = dict(
        all=("All Experiments", "SELECT * FROM STATUS ORDER BY EXPID DESC;"),
        active=(
            "Active Experiments",
            "SELECT * FROM STATUS WHERE STATUS='TRAINING' ORDER BY EXPID DESC;",
        ),
    )

    status_signal = Signal(str)
    progress_signal = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QVBoxLayout(self)

        self.query_selector = QComboBox()
        self.layout.addWidget(self.query_selector)

        for k, (n, q) in self.QUERIES.items():
            self.query_selector.addItem(n, userData=q)
        self.query_selector.currentIndexChanged.connect(self.query_changed)

        search_box = QWidget()
        self.layout.addWidget(search_box)
        search_box.layout = QHBoxLayout(search_box)
        search_text_input = QLineEdit()
        search_button = QPushButton("Search")
        search_button.clicked.connect(lambda: self.search(search_text_input.text()))
        search_box.layout.addWidget(search_text_input)
        search_box.layout.addWidget(search_button)
        search_text_input.setPlaceholderText(
            'Search! e.g. "RegressExp !PLS" -> "RegressExp" AND NOT "PLS"'
        )

        self.experiments_view = QTreeWidget()
        self.layout.addWidget(self.experiments_view)
        cols = ["Exp. ID", "Status", "Groups"]
        self.experiments_view.setColumnCount(len(cols))
        self.experiments_view.setHeaderLabels(cols)
        header = self.experiments_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.experiments_view.setSelectionBehavior(QTreeWidget.SelectRows)
        self.experiments_view.setSelectionMode(
            QTreeWidget.SelectionMode.ExtendedSelection
        )
        self.experiments_view.doubleClicked.connect(self.view_or_compare_exp)
        self.experiments_view.itemSelectionChanged.connect(self.exp_selection_changed)

        btn_box = QWidget()
        btn_box.layout = QHBoxLayout(btn_box)
        self.view_button = QPushButton()
        self.delete_button = QPushButton("Delete Exp")
        self.delete_button.clicked.connect(self.delete_selected)
        self.group_button = QPushButton("Group")
        self.group_button.clicked.connect(self.edit_groups)
        btn_box.layout.addWidget(self.view_button)
        btn_box.layout.addWidget(self.delete_button)
        btn_box.layout.addWidget(self.group_button)
        self.layout.addWidget(btn_box)
        self.view_button.clicked.connect(self.view_or_compare_exp)

        self.query_changed(0)
        self.exp_selection_changed()

    def edit_groups(self):
        expids = self.get_selected_experiments()
        dia = GroupEditDialog(self, expids)
        dia.groups_changed.connect(self.refresh_groups)
        dia.show()

    def get_selected_experiments(self) -> List[str]:
        selection = self.experiments_view.selectedItems()
        expids = []
        for item in selection:
            es = item.data(0, Qt.UserRole)
            if es is not None:
                expids.extend(es)
        expids = sorted(set(expids))
        return expids

    def delete_selected(self):
        exp_ids = self.get_selected_experiments()
        DBMethod(
            Database.delete_experiment,
            *[(e,) for e in exp_ids],
            slot=self.remove_expid_from_table,
        ).start()

    def remove_expid_from_table(self, expid):
        raise NotImplementedError
        items = self.experiments_view.findItems(expid, Qt.MatchFlag.MatchExactly & 1)
        rows = set(i.row() for i in items)
        assert len(rows) == 1
        self.table_experiments.removeRow(list(rows)[0])

    def exp_selection_changed(self):
        exps = self.get_selected_experiments()
        if len(exps):
            if len(exps) > 1:
                ttl = "Compare experiments"
            else:
                ttl = "View experiment"
            self.view_button.setEnabled(True)
            self.group_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            ttl = "No experiment selected"
            self.view_button.setEnabled(False)
            self.group_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        self.view_button.setText(ttl)

    def view_or_compare_exp(self):
        exps = self.get_selected_experiments()
        if exps:
            ExpCompareAndViewDialog(self, exps).show()
        else:
            print("No experiments")

    def run_query(self, query: Union[str, sql.Composable]):
        self.experiments_view.clear()
        self.set_status("Querying database...")
        self.set_progress(10)

        query = DBQuery(query)
        query.results_returned.connect(self.display_experiments)
        query.start()

    @staticmethod
    def parse_sql_from_search(sq: str) -> sql.Literal:
        parts = sq.split(" ")
        condition = sql.SQL("")

        for i, part in enumerate(parts):
            if part.startswith("!"):
                part = part[1:]
                negative = True
            else:
                negative = False
            term = sql.Literal(f"%{part}%")
            c = sql.SQL(
                " (STATUS.EXPID IN (SELECT EXPID FROM EXPGROUPS WHERE GROUPNAME LIKE {term}) "
                "OR STATUS.EXPID LIKE {term}"
                "OR STATUS.STATUS LIKE {term}) "
            )
            if i:
                condition += sql.SQL(" AND ")
            if negative:
                condition += sql.SQL(" NOT ")
            condition += c.format(term=term)

        return condition

    def search(self, search_query: str):
        query = sql.SQL("SELECT * FROM STATUS WHERE {condition} ORDER BY EXPID DESC;")
        condition = self.parse_sql_from_search(search_query)
        self.run_query(query.format(condition=condition))

    def query_changed(self, _: int):
        self.run_query(self.query_selector.currentData())

    def display_experiments(self, rows):
        FOLD_RE = re.compile(r"(.*)_(fold_?\d+|final|mean)")
        exps = {}
        for (expid, status) in rows:
            m = FOLD_RE.match(expid)
            if m:
                base_expid = m.group(1)
                if base_expid not in exps:
                    exps[base_expid] = []
                exps[base_expid].append((expid, status))
            else:
                exps[expid] = [(expid, status)]

        n = len(exps)
        if n:
            for i, (base_expid, data) in enumerate(exps.items()):
                all_status = set([s for _, s in data])
                all_status = ", ".join(sorted(all_status))
                wi = QTreeWidgetItem([f"{base_expid}x{len(data)}", all_status])
                wi.setData(0, Qt.UserRole, [e for e, _ in data])
                self.experiments_view.addTopLevelItem(wi)
                for (expid, status) in data:
                    cwi = QTreeWidgetItem([expid, status])
                    cwi.setData(0, Qt.UserRole, [expid])
                    wi.addChild(cwi)
        else:
            self.set_status("No experiments found!")

        self.set_progress(100)

        self.refresh_groups()

    def refresh_groups(self):
        DBQuery("SELECT * FROM EXPGROUPS;", self.display_groups).start()

    def display_groups(self, rv):
        groups_by_exp = {}
        for e, g in rv:
            if e not in groups_by_exp:
                groups_by_exp[e] = []
            groups_by_exp[e].append(g)

        for i in range(self.experiments_view.topLevelItemCount()):
            tli = self.experiments_view.topLevelItem(i)
            tli_groups = set()
            for j in range(tli.childCount()):
                ci = tli.child(j)
                expid = ci.data(0, Qt.UserRole)[0]
                try:
                    groups = groups_by_exp[expid]
                    tli_groups.update(groups)
                    ci.setText(2, " | ".join(groups))
                except KeyError:
                    pass
            if tli_groups:
                tli.setText(2, " | ".join(sorted(tli_groups)))

    def populate_groups(self, groups):
        for group, *_ in set(groups):
            self.query_selector.addItem(
                f"Group {group}",
                userData=f"SELECT STATUS.EXPID, STATUS.STATUS FROM STATUS INNER JOIN EXPGROUPS ON STATUS.EXPID = EXPGROUPS.EXPID WHERE GROUPNAME='{group}';",
            )

    def set_status(self, s: str):
        self.status_signal.emit(s)

    def set_progress(self, p: int):
        self.progress_signal.emit(p)
