from typing import List

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QPushButton
from PySide6.QtCore import Signal

from mldb import Database

from .db_iop import DBQuery, DBMethod
from .exp_view import ExpViewDialog
from .exp_compare import ExpCompareDialog
from .edit_groups import GroupEditDialog


class ExperimentListWidget(QWidget):

    QUERIES = dict(
        all=('All Experiments', 'SELECT * FROM STATUS;'),
        active=('Active Experiments', 'SELECT * FROM STATUS WHERE STATUS=\'TRAINING\';'),
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

        self.table_experiments = QTableWidget()
        self.layout.addWidget(self.table_experiments)
        cols = ['Exp. ID', 'Status', 'Groups']
        self.table_experiments.setColumnCount(len(cols))
        self.table_experiments.setHorizontalHeaderLabels(cols)
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
        self.group_button = QPushButton('Group')
        self.group_button.clicked.connect(self.edit_groups)
        btn_box.layout.addWidget(self.view_button)
        btn_box.layout.addWidget(self.delete_button)
        btn_box.layout.addWidget(self.group_button)
        self.layout.addWidget(btn_box)
        self.view_button.clicked.connect(self.view_or_compare_exp)

        self.query_changed(0)
        self.exp_selection_changed()
        DBQuery('SELECT GROUPNAME FROM EXPGROUPS;', self.populate_groups).start()

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
        if len(exps) == 1:
            ExpViewDialog(self, exps[0]).show()
        elif len(exps) > 1:
            ExpCompareDialog(self, exps).show()
        else:
            print('No experiments')

    def run_query(self, query: str):
        # self.table_experiments.clear()
        self.table_experiments.setRowCount(0)
        self.set_status('Querying database...')
        self.set_progress(10)

        query = DBQuery(query)
        query.results_returned.connect(self.display_experiments)
        query.start()

    def query_changed(self, _: int):
        self.run_query(self.query_selector.currentData())

    def display_experiments(self, rows):
        # self.table_experiments.clear()
        n = len(rows)
        self.table_experiments.setRowCount(n)
        dp = 100//n
        for i, (expid, status) in enumerate(reversed(rows)):
            self.table_experiments.setItem(i, 0, QTableWidgetItem(expid))
            self.table_experiments.setItem(i, 1, QTableWidgetItem(status))
            self.set_progress((i + 1)*dp)
        self.set_progress(100)
        self.set_status('')

        if self.models is None:
            # No model cache, likely this is the first call
            # so this is the all exp query and can use it to populate models
            self.populate_models([e for e, _ in rows])
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
            self.table_experiments.setItem(i, 2, QTableWidgetItem(groups))

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
