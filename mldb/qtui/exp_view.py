import numpy as np
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)

from .plot_widget import PlotWidget
from .exp_views import ExpLossAndLRView, ExpConfigView, MetricsView
from .db_iop import DBExpMetrics, DBExpQualResults


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

        self.tabs.addTab(ExpConfigView(expid), 'Config')
        self.tabs.addTab(ExpLossAndLRView(expid), 'Loss v Epoch')
        self.tabs.addTab(MetricsView(expid), 'Metrics')

        self.setWindowTitle(f'{expid} - Details')

        DBExpQualResults(self.expid, self.qualres_returned).start()

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
