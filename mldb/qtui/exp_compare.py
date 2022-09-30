from typing import List

import numpy as np
from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QTabWidget

from .plot_widget import PlotWidget
from .db_iop import DBExpDetails, DBExpMetrics


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

        self.metrics_low_plot = PlotWidget()
        self.metrics_low_plot.axes.set_title('Metrics (lower is better)')
        self.plots.addTab(self.metrics_low_plot, 'Metrics (errors)')

        self.metrics_high_plot = PlotWidget()
        self.metrics_high_plot.axes.set_title('Metrics (higher is better)')
        self.plots.addTab(self.metrics_high_plot, 'Metrics (correlations)')

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

    def plot_metrics(self):
        assert len(self.metrics_by_exp) == len(self.expids)

        self.low_metrics = sorted(self.low_metrics)
        self.high_metrics = sorted(self.high_metrics)

        w = 1. / len(self.expids)

        for i, expid in enumerate(self.expids):
            colour = f'C{i}'
            low_x = np.arange(len(self.low_metrics))+np.random.uniform(-0.1, 0.1, len(self.low_metrics))
            low_y = list([self.metrics_by_exp[expid].get(n, float('nan')) for n in self.low_metrics])
            self.metrics_low_plot.axes.plot(
                low_x, low_y, 'o', color=colour
            )

            high_x = np.arange(len(self.high_metrics))+np.random.uniform(-0.1, 0.1, len(self.high_metrics))
            high_y = list([self.metrics_by_exp[expid].get(n, float('nan')) for n in self.high_metrics])
            self.metrics_high_plot.axes.plot(
                high_x, high_y, 'o', color=colour
            )

        ne = len(self.expids)
        low_lbl_x = np.arange(len(self.low_metrics))
        low_labels = [
            # ('\n'*(i % 2)) +
            (t
             .replace('metrics.', '')
             .replace('test', 'Te')
             .replace('valid', 'V'))
            for i, t in enumerate(self.low_metrics)
        ]
        self.metrics_low_plot.axes.set_xticks(
            low_lbl_x,
            low_labels,
            rotation=45,
            ha='right', va='top'
        )
        self.metrics_low_plot.axes.set_yscale('log')
        self.metrics_low_plot.redraw_and_flush()

        high_lbl_x = np.arange(len(self.high_metrics))
        high_labels = [
            # ('\n' * (i % 2)) +
            (t
             .replace('metrics.', '')
             .replace('test', 'Te')
             .replace('valid', 'V'))
            for i, t in enumerate(self.high_metrics)
        ]
        self.metrics_high_plot.axes.set_xticks(
            high_lbl_x,
            high_labels,
            rotation=45,
            ha='right', va='top'
        )
        self.metrics_high_plot.redraw_and_flush()


