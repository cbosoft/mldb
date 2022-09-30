import numpy as np
from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel, QTabWidget, QFormLayout

from .plot_widget import PlotWidget

from .db_iop import DBExpDetails, DBExpMetrics, DBExpQualResults, DBExpHyperParams


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

        self.loss_plot = PlotWidget(ax_rect=(0.2, 0.2, 0.6, 0.7))
        self.loss_plot.axes.set_title('Loss v Epoch')
        self.loss_plot.axes.set_xscale('log')
        self.loss_plot.axes.set_yscale('log')
        self.loss_plot.axes.set_title('Loss v Epoch')
        self.lr_ax = self.loss_plot.axes.twinx()
        self.lr_ax.set_ylabel('Learning rate')
        self.tabs.addTab(self.loss_plot, 'Loss v Epoch')

        self.metrics_low_plot = PlotWidget()
        self.metrics_low_plot.axes.set_title('Metrics (lower is better)')
        self.tabs.addTab(self.metrics_low_plot, 'Metrics (errors)')

        self.metrics_high_plot = PlotWidget()
        self.metrics_high_plot.axes.set_title('Metrics (higher is better)')
        self.tabs.addTab(self.metrics_high_plot, 'Metrics (correlations)')

        self.setWindowTitle(f'{expid} - Details')

        DBExpDetails(self.expid, self.details_returned).start()
        DBExpMetrics(self.expid, self.metrics_returned).start()
        DBExpQualResults(self.expid, self.qualres_returned).start()
        DBExpHyperParams(self.expid, self.hparams_returned).start()

    def details_returned(self, d: dict):
        self.loss_plot.clear()
        self.exp_details.layout.addRow('Status', QLabel(d['status']))

        try:
            train_losses = d['losses']['train']['loss']
            train_epochs = d['losses']['train']['epoch']
            self.loss_plot.plot(train_epochs, train_losses, label='training')
        except KeyError as e:
            print(e)

        try:
            valid_losses = d['losses']['valid']['loss']
            valid_epochs = d['losses']['valid']['epoch']
            self.loss_plot.plot(valid_epochs, valid_losses, label='valid')
        except KeyError as e:
            print(e)

        self.loss_plot.axes.set_xlabel('Epoch [#]')
        self.loss_plot.axes.set_ylabel('Loss')

        try:
            lr_epochs = d['lrs']['epochs']
            lrs = d['lrs']['lrs']
            self.lr_ax.plot(lr_epochs, lrs, zorder=-10, color='k', ls='--')
        except KeyError as e:
            print(e)

        self.loss_plot.legend()
        self.loss_plot.redraw_and_flush()

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

        low_x = list(range(len(low_metrics)))
        low_y = list(low_metrics.values())
        low_labels = list(low_metrics.keys())
        self.metrics_low_plot.axes.bar(
            low_x, low_y
        )
        self.metrics_low_plot.axes.set_xticks(
            low_x,
            low_labels,
            rotation=45,
        )
        self.metrics_low_plot.redraw_and_flush()

        high_x = list(range(len(high_metrics)))
        high_y = list(high_metrics.values())
        high_labels = list(high_metrics.keys())
        self.metrics_high_plot.axes.bar(
            high_x, high_y
        )
        self.metrics_high_plot.axes.set_xticks(
            high_x,
            high_labels,
            rotation=45,
        )
        self.metrics_high_plot.redraw_and_flush()

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
                w.axes.plot(bins, t, '--', color=colour)
                w.axes.plot(bins, o, color=colour)
            w.redraw_and_flush()
            self.tabs.addTab(w, f'QualRes: {plotid}')

    def hparams_returned(self, h):
        for k, v in h.items():
            self.exp_details.layout.addRow(k, QLabel(v))
