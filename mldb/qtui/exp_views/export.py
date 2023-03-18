from collections import defaultdict
import os.path

from PySide6.QtWidgets import QPushButton, QVBoxLayout, QFileDialog, QMessageBox

import psycopg2.sql as sql
import numpy as np

from .view_base import BaseExpView
from ..db_iop import DBQuery


class ExportData(BaseExpView):
    def __init__(self, *expids):
        super().__init__(*expids)
        self.layout = QVBoxLayout(self)
        self.btn = QPushButton("Export")
        self.btn.setEnabled(False)
        self.btn.clicked.connect(self.export_data)
        self.layout.addWidget(self.btn)

        self.last_dir = "/Users/christopherboyle/gits/mdpc/CLD2QC/exported_exp_data"
        self.data = {}
        self.exp_groups = {}

        self.refresh()

    def refresh(self):
        self.data = {}
        self.btn.setEnabled(False)
        q = sql.SQL("SELECT * FROM METRICS WHERE {condition};")
        condition = sql.SQL("")
        for i, expid in enumerate(self.expids):
            expid = sql.Literal(expid)
            if i:
                condition += sql.SQL(" OR ")
            condition += sql.SQL(" EXPID={e} ").format(e=expid)
            # fewer rows return, but is slower!
            # condition += sql.SQL(
            #     "((EXPID, EPOCH) IN (SELECT EXPID, max(EPOCH) FROM METRICS WHERE EXPID={e} GROUP BY EXPID))"
            # ).format(e=expid)
        DBQuery(q.format(condition=condition), self.metrics_returned).start()

    def metrics_returned(self, rows):
        data_by_exp_epoch = defaultdict(lambda: defaultdict(dict))
        for expid, epoch, kind, value in rows:
            data_by_exp_epoch[expid][epoch][kind] = value

        latest_data_by_exp = {}
        for expid, epoch_data in data_by_exp_epoch.items():
            latest_data = epoch_data[sorted(epoch_data)[-1]]
            latest_data_by_exp[expid] = latest_data

        self.data = latest_data_by_exp

        self.get_groups()

    def get_groups(self):
        q = sql.SQL("SELECT * FROM EXPGROUPS WHERE {condition};")
        condition = sql.SQL("")
        for i, expid in enumerate(self.expids):
            expid = sql.Literal(expid)
            if i:
                condition += sql.SQL(" OR ")
            condition += sql.SQL(" EXPID={e} ").format(e=expid)
        DBQuery(q.format(condition=condition), self.groups_returned).start()

    def groups_returned(self, rows):
        primary_groups_by_exp = {}
        for expid, group in rows:
            if "=" in group:
                primary_groups_by_exp[expid] = group

        for expid, pgroup in primary_groups_by_exp.items():
            gdata = {}
            for item in pgroup.split(";"):
                kv = item.split("=")
                if len(kv) > 1:
                    k, v = kv
                    if isinstance(v, str):
                        v = f'"{v}"'
                    gdata[k] = v
            if expid in self.data:
                mdata = self.data[expid]
                self.data[expid] = {**gdata, **mdata}

        self.btn.setEnabled(True)

    def export_data(self):
        fn, _ = QFileDialog.getSaveFileName(
            self, "location to save data", self.last_dir, "*.csv"
        )
        if fn:
            self.last_dir = os.path.dirname(fn)
            self.save_to_csv(fn)

    def data_as_table(self) -> list:
        rows = sorted(self.data)
        columns = list()  # list used instead of set to preserve order
        for edata in self.data.values():
            for k in edata:
                if k not in columns:
                    columns.append(k)

        table = [["", *columns]]
        for r, row in enumerate(rows):
            row_data = [row]
            for c, col in enumerate(columns):
                try:
                    row_data.append(self.data[row][col])
                except KeyError:
                    row_data.append("")
            table.append(row_data)
        return table

    def save_to_csv(self, fn):
        table = self.data_as_table()
        table_str = "\n".join([",".join([str(v) for v in row]) for row in table])

        with open(fn, "w") as f:
            f.write(table_str)

        mbox = QMessageBox(self)
        mbox.setWindowTitle("Done!")
        mbox.setText(f"Data has been written to {fn}")
        mbox.show()
