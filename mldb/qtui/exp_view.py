import numpy as np
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QLabel,
    QTextEdit,
    QTabWidget, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtGui import QTextOption

from .plot_widget import PlotWidget
from .exp_views import ExpLossAndLRView, ExpConfigView
from .db_iop import DBQuery, DBExpMetrics, DBExpQualResults, DBExpHyperParams


def plot_widget_and_table():
    w = QWidget()
    w.layout = QVBoxLayout(w)
    plt = PlotWidget()
    w.layout.addWidget(plt)
    tbl = QTableWidget()
    tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    w.layout.addWidget(tbl)
    return w, plt, tbl


class ExpViewDialog(QDialog):

    QUERY = ''

    def __init__(self, parent: QWidget, expid: str, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.expid = expid

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.exp_details = QWidget()
        self.exp_details.layout = QFormLayout(self.exp_details)
        self.exp_details.layout.addRow('Exp. ID', QLabel(expid))
        self.tabs.addTab(self.exp_details, 'Details')

        self.tabs.addTab(ExpConfigView(expid), 'Config')
        self.tabs.addTab(ExpLossAndLRView(expid), 'Loss v Epoch')

        self.final_metrics_low_widget, self.final_metrics_low_plot, self.final_metrics_low_table = plot_widget_and_table()
        self.final_metrics_low_plot.axes.set_title('Metrics (lower is better)')
        # self.tabs.addTab(final_metrics_low_widget, 'Final Metrics (errors)')

        self.final_metrics_high_widget, self.final_metrics_high_plot, self.final_metrics_high_table = plot_widget_and_table()
        self.final_metrics_high_plot.axes.set_title('Metrics (higher is better)')
        # self.tabs.addTab(final_metrics_high_widget, 'Final Metrics (correlations)')

        # best_metrics_low_widget, self.best_metrics_low_plot, self.best_metrics_low_table = plot_widget_and_table()
        # self.best_metrics_low_plot.axes.set_title('Metrics (lower is better)')
        # self.tabs.addTab(best_metrics_low_widget, 'Best Metrics (errors)')
        #
        # best_metrics_high_widget, self.best_metrics_high_plot, self.best_metrics_high_table = plot_widget_and_table()
        # self.best_metrics_high_plot.axes.set_title('Metrics (higher is better)')
        # self.tabs.addTab(best_metrics_high_widget, 'Best Metrics (correlations)')

        self.setWindowTitle(f'{expid} - Details')

        DBExpMetrics(self.expid, self.metrics_returned).start()
        DBExpQualResults(self.expid, self.qualres_returned).start()
        DBExpHyperParams(self.expid, self.hparams_returned).start()

    def metrics_returned(self, d: dict):
        low_metrics = {}
        high_metrics = {}

        if 'data' not in d:
            print('No metrics available.')
            return

        for m, v in d['data'].items():
            lowercase_m = m.lower()
            if 'error' in lowercase_m or 'mse' in lowercase_m:
                low_metrics[m] = v
            else:
                high_metrics[m] = v

        if low_metrics:
            low_x = list(range(len(low_metrics)))
            low_y = list(low_metrics.values())
            low_labels = list(low_metrics.keys())
            self.final_metrics_low_plot.axes.bar(
                low_x, low_y
            )
            self.final_metrics_low_plot.axes.set_xticks(
                low_x,
                low_labels,
                rotation=45,
            )
            self.final_metrics_low_plot.redraw_and_flush()
            self.final_metrics_low_table.clear()
            self.final_metrics_low_table.setColumnCount(2)
            self.final_metrics_low_table.setRowCount(len(low_labels))
            for i, (k, v) in enumerate(zip(low_labels, low_y)):
                self.final_metrics_low_table.setItem(i, 0, QTableWidgetItem(k))
                self.final_metrics_low_table.setItem(i, 1, QTableWidgetItem(f'{v}'))
            self.tabs.addTab(self.final_metrics_low_widget, 'Final Metrics (errors)')

        if high_metrics:
            high_x = list(range(len(high_metrics)))
            high_y = list(high_metrics.values())
            high_labels = list(high_metrics.keys())
            self.final_metrics_high_plot.axes.bar(
                high_x, high_y
            )
            self.final_metrics_high_plot.axes.set_xticks(
                high_x,
                high_labels,
                rotation=45,
            )
            self.final_metrics_high_plot.redraw_and_flush()
            self.tabs.addTab(self.final_metrics_high_widget, 'Final Metrics (correlations)')

    def qualres_returned(self, q):
        for plotid, qualres in q:
            w = PlotWidget()
            w.axes.set_xlabel(qualres['xlabel'])
            w.axes.set_ylabel(qualres['ylabel'])
            w.axes.set_xscale(qualres['xscale'])
            data = qualres['data']
            last_epoch = max([d['epoch'] for d in data])
            initial_data = [d for d in data if d['epoch'] == 0]
            outputs = [d['output'] for d in data if d['epoch'] == last_epoch]
            targets = [d['target'] for d in initial_data]
            edges = np.geomspace(1, 1e3, 101)
            bins = (edges[1:]*edges[:-1])**0.5
            for i, (t, o) in enumerate(zip(targets, outputs)):
                colour = f'C{i}'
                w.axes.plot(bins, np.squeeze(t), '--', color=colour)
                w.axes.plot(bins, np.squeeze(o), color=colour)
            w.redraw_and_flush()
            self.tabs.addTab(w, f'QualRes: {plotid}')

    def hparams_returned(self, h):
        for k, v in h.items():
            self.exp_details.layout.addRow(k, QLabel(v))
