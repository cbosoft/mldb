from typing import List

import numpy as np
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QDialog,
    QVBoxLayout, QHBoxLayout,
    QSpinBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)

from .plot_widget import PlotWidget
from .db_iop import DBExpDetails, DBExpMetrics


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


class ExpCompareDialog(QDialog):

    QUERY = ''

    def __init__(self, parent: QWidget, expids: List[str], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.expids = expids

        self.layout = QVBoxLayout(self)

        self.plots = QTabWidget()
        self.layout.addWidget(self.plots)

        self.loss_plot = PlotWidget()
        self.loss_plot.axes.set_title('Loss v Epoch')
        self.loss_plot.axes.set_xscale('log')
        self.loss_plot.axes.set_yscale('log')
        self.loss_plot.axes.set_title('Loss v Epoch')
        self.plots.addTab(self.loss_plot, 'Loss v Epoch')

        final_metrics_low_widget, self.final_metrics_low_plot, self.final_metrics_low_table, self.final_metrics_low_groups = plot_widget_and_table(grouping_table=True)
        self.low_metrics_grouping = {}
        self.final_metrics_low_groups: GroupTable
        self.final_metrics_low_groups.groups_changed.connect(self.low_grouping_changed)
        self.final_metrics_low_plot.axes.set_title('Metrics (lower is better)')
        self.plots.addTab(final_metrics_low_widget, 'Final Metrics (errors)')

        final_metrics_high_widget, self.final_metrics_high_plot, self.final_metrics_high_table = plot_widget_and_table()
        self.final_metrics_high_plot.axes.set_title('Metrics (higher is better)')
        self.plots.addTab(final_metrics_high_widget, 'Final Metrics (correlations)')

        self.low_metrics = set()
        self.high_metrics = set()
        self.metrics_by_exp = {}

        for expid in expids:
            DBExpDetails(expid, self.details_returned).start()
            DBExpMetrics(expid, self.metrics_returned).start()

    def details_returned(self, d: dict):

        expid = d['expid']
        i = self.expids.index(expid)
        colour = f'C{i}'

        train_losses = d['losses']['train']['loss']
        train_epochs = d['losses']['train']['epoch']
        valid_losses = d['losses']['valid']['loss']
        valid_epochs = d['losses']['valid']['epoch']
        # self.loss_plot.clear()
        self.loss_plot.plot(train_epochs, train_losses, ls='-', color=colour, label=expid)
        self.loss_plot.plot(valid_epochs, valid_losses, ls=':', color=colour, alpha=0.5)
        self.loss_plot.axes.set_xlabel('Epoch [#]')
        self.loss_plot.axes.set_ylabel('Loss')
        self.loss_plot.legend()
        self.loss_plot.redraw_and_flush()

    def metrics_returned(self, d: dict):

        expid = d['expid']

        for m, v in d['data'].items():
            lowercase_m = m.lower()
            if 'error' in lowercase_m or 'mse' in lowercase_m:
                self.low_metrics.add(m)
            else:
                self.high_metrics.add(m)

        self.metrics_by_exp[expid] = d['data']
        if len(self.metrics_by_exp) == len(self.expids):
            self.plot_metrics()
            for expid in self.expids:
                self.final_metrics_low_groups.add_expid(expid)

    def low_grouping_changed(self, groups: dict):
        self.low_metrics_grouping = groups
        self.plot_metrics()

    def plot_metrics_set(self, plot_widget: PlotWidget, table: QTableWidget, metrics_set: list, groupings: dict):
        table.clear()
        table.setColumnCount(2)
        table.setRowCount((len(self.expids)+1)*len(self.low_metrics))
        labels = [
            # ('\n'*(i % 2)) +
            (t
             .replace('metrics.', '')
             .replace('test', 'Te')
             .replace('valid', 'V')
             .replace('MeanAbsoluteError', 'MAE'))
            for i, t in enumerate(metrics_set)
        ]

        plot_widget.clear()
        if not groupings:
            for i, expid in enumerate(self.expids):
                colour = f'C{i}'
                x = np.arange(len(metrics_set))+np.random.uniform(-0.1, 0.1, len(metrics_set))
                y = list([self.metrics_by_exp[expid].get(n, float('nan')) for n in metrics_set])
                plot_widget.axes.plot(
                    x, y, 'o', color=colour
                )

            for i, expid in enumerate(self.expids):
                for j, (k, kk) in enumerate(zip(labels, metrics_set)):
                    v = self.metrics_by_exp[expid].get(kk, float('nan'))
                    table.setItem((i+1)*len(self.low_metrics) + j, 0, QTableWidgetItem(f'{expid}/{k}'))
                    table.setItem((i+1)*len(self.low_metrics) + j, 1, QTableWidgetItem(f'{v}'))

            for i, k in enumerate(metrics_set):
                v = sum([self.metrics_by_exp[e].get(k, float('nan')) for e in self.expids])/len(self.expids)
                table.setItem(i, 0, QTableWidgetItem(f'mean/{k}'))
                table.setItem(i, 1, QTableWidgetItem(f'{v}'))
                plot_widget.axes.plot(
                    [i-0.2, i+0.2], [v, v], '--', color='k'
                )
        else:
            exp_by_group = {}
            for expid, group in groupings.items():
                if group not in exp_by_group:
                    exp_by_group[group] = list()
                exp_by_group[group].append(expid)

            for i, group in enumerate(sorted(exp_by_group)):
                expids = exp_by_group[group]
                x, y = [], []
                for exp in expids:
                    for j, m in enumerate(metrics_set):
                        x.append(j)
                        y.append(self.metrics_by_exp[exp].get(m, float('nan')))
                plot_widget.axes.plot(
                    x, y, 'o', color=f'C{i}'
                )
        lbl_x = np.arange(len(metrics_set))
        plot_widget.axes.set_xticks(
            lbl_x, labels,
        )
        plot_widget.axes.set_yscale('log')
        plot_widget.redraw_and_flush()

    def plot_metrics(self):
        assert len(self.metrics_by_exp) == len(self.expids)
        self.plot_metrics_set(self.final_metrics_low_plot, self.final_metrics_low_table, sorted(self.low_metrics), self.low_metrics_grouping)


