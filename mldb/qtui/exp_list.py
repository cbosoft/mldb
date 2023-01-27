from typing import List, Union

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QHeaderView
)
from PySide6.QtCore import Signal, Qt
import psycopg2.sql

from .db_iop import DBQuery, DBMethod, Database
from .exp_compare_and_vew import ExpCompareAndViewDialog
from .edit_groups import GroupEditDialog


class ExperimentListWidget(QWidget):
    QUERIES = dict(
        all=('All Experiments', 'SELECT * FROM STATUS ORDER BY EXPID DESC;'),
        active=('Active Experiments', 'SELECT * FROM STATUS WHERE STATUS=\'TRAINING\' ORDER BY EXPID DESC;'),
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
        search_button = QPushButton('Search')
        search_button.clicked.connect(lambda: self.search(search_text_input.text()))
        search_box.layout.addWidget(search_text_input)
        search_box.layout.addWidget(search_button)

        self.table_experiments = QTableWidget()
        self.layout.addWidget(self.table_experiments)
        cols = ['Exp. ID', 'Status', 'Groups']
        self.table_experiments.setColumnCount(len(cols))
        self.table_experiments.setHorizontalHeaderLabels(cols)
        header = self.table_experiments.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        # self.table_experiments.horizontalHeader().section(True)
        # self.table_experiments.horizontalHeader().setDefaultSectionSize(400)
        self.table_experiments.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_experiments.doubleClicked.connect(self.view_or_compare_exp)
        self.table_experiments.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_experiments.itemSelectionChanged.connect(self.exp_selection_changed)

        btn_box = QWidget()
        btn_box.layout = QHBoxLayout(btn_box)
        self.view_button = QPushButton()
        self.delete_button = QPushButton('Delete Exp')
        self.delete_button.clicked.connect(self.delete_selected)
        self.group_button = QPushButton('Group')
        self.group_button.clicked.connect(self.edit_groups)
        btn_box.layout.addWidget(self.view_button)
        btn_box.layout.addWidget(self.delete_button)
        btn_box.layout.addWidget(self.group_button)
        self.layout.addWidget(btn_box)
        self.view_button.clicked.connect(self.view_or_compare_exp)

        self.query_changed(0)
        self.exp_selection_changed()

        self.models = None

    def edit_groups(self):
        selection = self.table_experiments.selectedIndexes()
        expids = [i.data() for i in selection if i.column() == 0]
        dia = GroupEditDialog(self, expids)
        dia.groups_changed.connect(self.refresh_groups)
        dia.show()

    def get_selected_experiments(self) -> List[str]:
        selection = self.table_experiments.selectedIndexes()
        selection = [i.data() for i in selection if i.column() == 0]
        return selection

    def delete_selected(self):
        exp_ids = self.get_selected_experiments()
        DBMethod(
            Database.delete_experiment,
            *[(e,) for e in exp_ids],
            slot=self.remove_expid_from_table
        ).start()

    def remove_expid_from_table(self, expid):
        items = self.table_experiments.findItems(expid, Qt.MatchFlag.MatchExactly & 1)
        rows = set(i.row() for i in items)
        assert len(rows) == 1
        self.table_experiments.removeRow(list(rows)[0])

    def exp_selection_changed(self):
        exps = self.get_selected_experiments()
        if len(exps):
            if len(exps) > 1:
                ttl = 'Compare experiments'
            else:
                ttl = 'View experiment'
            self.view_button.setEnabled(True)
            self.group_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            ttl = 'No experiment selected'
            self.view_button.setEnabled(False)
            self.group_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        self.view_button.setText(ttl)

    def view_or_compare_exp(self):
        exps = self.get_selected_experiments()
        if exps:
            ExpCompareAndViewDialog(self, exps).show()
        else:
            print('No experiments')

    def run_query(self, query: Union[str, psycopg2.sql.Composable]):
        # self.table_experiments.clear()
        self.table_experiments.setRowCount(0)
        self.set_status('Querying database...')
        self.set_progress(10)

        query = DBQuery(query)
        query.results_returned.connect(self.display_experiments)
        query.start()

    @staticmethod
    def parse_sql_from_search(sq: str) -> psycopg2.sql.Literal:
        sq = sq.replace(' ', '%')
        sq = f'%{sq}%'
        return psycopg2.sql.Literal(sq)

    def search(self, search_query: str):
        condition = self.parse_sql_from_search(search_query)
        query = 'SELECT * FROM STATUS WHERE STATUS.EXPID IN ' \
                '(SELECT EXPID FROM EXPGROUPS WHERE GROUPNAME LIKE {condition}) ' \
                'OR STATUS.EXPID LIKE {condition}' \
                'OR STATUS.STATUS LIKE {condition}' \
                'ORDER BY EXPID DESC;'
        query = psycopg2.sql.SQL(query).format(condition=condition)
        self.run_query(query)

    def query_changed(self, _: int):
        self.run_query(self.query_selector.currentData())

    def display_experiments(self, rows):
        n = len(rows)
        self.table_experiments.setRowCount(n)
        if n:
            for i, (expid, status) in enumerate(rows):
                expid_wi = QTableWidgetItem(expid)
                expid_wi.setToolTip(expid)
                status_wi = QTableWidgetItem(status)
                status_wi.setToolTip(status)
                self.table_experiments.setItem(i, 0, expid_wi)
                self.table_experiments.setItem(i, 1, status_wi)
            self.set_status(f'{n} experiments found.')
        else:
            self.set_status('No experiments found!')

        self.set_progress(100)

        # if self.models is None:
        #     # No model cache, likely this is the first call
        #     # so this is the all exp query and can use it to populate models
        #     self.populate_models([e for e, _ in rows])

        self.refresh_groups()

    def refresh_groups(self):
        DBQuery('SELECT * FROM EXPGROUPS;', self.display_groups).start()

    def display_groups(self, rv):
        groups_by_exp = {}
        for e, g in rv:
            if e not in groups_by_exp:
                groups_by_exp[e] = []
            groups_by_exp[e].append(g)

        for i in range(self.table_experiments.rowCount()):
            e = self.table_experiments.item(i, 0).text()
            if e in groups_by_exp:
                groups = ', '.join(groups_by_exp[e])
            else:
                groups = ''
            groups_wi = QTableWidgetItem(groups)
            groups_wi.setToolTip(groups)
            self.table_experiments.setItem(i, 2, groups_wi)

    def populate_models(self, expids):
        assert self.models is None
        self.models = set()
        for expid in expids:
            model_name = (expid
                          .replace('_', '')
                          .replace('-', '')
                          .replace('fold', '')
                          .strip('0123456789'))
            self.models.add(model_name)

        for model in self.models:
            self.query_selector.addItem(
                f'Model {model}',
                userData=f'SELECT * FROM STATUS WHERE EXPID LIKE \'%%{model}%%\'')

    def populate_groups(self, groups):
        for group, *_ in set(groups):
            self.query_selector.addItem(
                f'Group {group}',
                userData=f'SELECT STATUS.EXPID, STATUS.STATUS FROM STATUS INNER JOIN EXPGROUPS ON STATUS.EXPID = EXPGROUPS.EXPID WHERE GROUPNAME=\'{group}\';')

    def set_status(self, s: str):
        self.status_signal.emit(s)

    def set_progress(self, p: int):
        self.progress_signal.emit(p)
