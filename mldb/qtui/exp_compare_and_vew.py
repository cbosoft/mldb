from typing import List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
)

from .plot_widget import PlotWidget
from .exp_views import (
    ExpLossAndLRView,
    ExpConfigView,
    MetricsView,
    ExpQualresView,
    ExportData,
)


class GroupTable(QTableWidget):
    groups_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expids = []
        self.groups = {}

    def add_expid(self, expid):
        self.expids.append(expid)
        self.refresh()

    def refresh(self):
        self.clear()
        self.setColumnCount(2)
        self.setRowCount(len(self.expids))

        for i, expid in enumerate(self.expids):
            self.setItem(i, 0, QTableWidgetItem(expid))
            groupbox = QSpinBox()
            self.setCellWidget(i, 1, groupbox)
            groupbox.valueChanged.connect(lambda v, e=expid: self.set_group(e, v))

    def set_group(self, expid, group):
        self.groups[expid] = group
        if group == 0:
            if expid in self.groups:
                self.groups.pop(expid)
        self.groups_changed.emit(self.groups)


def plot_widget_and_table(grouping_table=False):
    w = QWidget()
    w.layout = QVBoxLayout(w)
    plt = PlotWidget()
    w.layout.addWidget(plt)
    if grouping_table:
        hw = QWidget()
        hw.layout = QHBoxLayout(hw)
        w.layout.addWidget(hw)
        tbl = QTableWidget()
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl_grouping = GroupTable()
        hw.layout.addWidget(tbl)
        hw.layout.addWidget(tbl_grouping)
        return w, plt, tbl, tbl_grouping
    else:
        tbl = QTableWidget()
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        w.layout.addWidget(tbl)
        return w, plt, tbl


class ExpCompareAndViewDialog(QDialog):
    QUERY = ""

    def __init__(self, parent: QWidget, expids: List[str], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.expids = expids
        self.resize(1280, 720)

        if len(self.expids) == 1:
            title = self.expids[0]
        else:
            title = ', '.join(self.expids)[:50] + '...'
        self.setWindowTitle(title)

        self.layout = QVBoxLayout(self)
        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.refresh)
        self.layout.addWidget(refresh_button)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.views = {
            "Config": ExpConfigView(*expids),
            "Loss Curve": ExpLossAndLRView(*expids),
            "Metrics": MetricsView(*expids),
            "Qualitative Results": ExpQualresView(*expids),
            "Export": ExportData(*expids),
        }

        for tabname, widget in self.views.items():
            self.tabs.addTab(widget, tabname)
    
    def refresh(self):
        for view in self.views.values():
            try:
                view.refresh()
            except Exception as e:
                print(view, e)
