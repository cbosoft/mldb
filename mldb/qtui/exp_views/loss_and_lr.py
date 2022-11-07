import matplotlib.pyplot as plt
from PySide6.QtWidgets import QHBoxLayout
import numpy as np

from ..plot_widget import PlotWidget
from ..db_iop import DBExpDetails
from .view_base import BaseExpView


class ExpLossAndLRView(BaseExpView):

    def __init__(self, *expids: str):
        super().__init__(*expids)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # plot of loss against epoch, with secondary axis showing learning rate.
        self.plot = PlotWidget(ax_rect=(0.2, 0.2, 0.6, 0.7))
        self.loss_ax = self.plot.axes
        self.loss_ax.set_yticks([])
        self.loss_ax.set_title('Loss v Epoch')
        self.loss_ax.set_xlabel('Epoch [#]')
        self.loss_ax.set_ylabel('Loss [AU]')
        self.lr_ax = self.plot.axes.twinx()
        self.lr_ax.set_ylabel('Learning rate')
        self.layout.addWidget(self.plot)

        self.refresh()
        self.i = 0.0

    def refresh(self):
        self.plot.clear()
        self.i = 0.0
        for expid in self.expids:
            DBExpDetails(expid, self.details_returned).start()

    def details_returned(self, d: dict):

        expid = d['expid']

        try:
            train_losses = d['losses']['train']['loss']
            train_epochs = d['losses']['train']['epoch']
        except KeyError:
            print(f'No training losses for {expid}')
            train_losses = None
            train_epochs = None

        try:
            valid_losses = d['losses']['valid']['loss']
            valid_epochs = d['losses']['valid']['epoch']
        except KeyError:
            print(f'No validation losses for {expid}')
            valid_losses = None
            valid_epochs = None

        try:
            lr_epochs = d['lrs']['epochs']
            lr_values = d['lrs']['lrs']
        except KeyError:
            print(f'No learning rate info for {expid}')
            lr_epochs = None
            lr_values = None

        self.update_plots(
            expid,
            train_epochs, train_losses,
            valid_epochs, valid_losses,
            lr_epochs, lr_values
        )

    def update_plots(self, expid, t_e, t_l, v_e, v_l, lr_e, lr_v):

        t_l = np.log10(t_l)
        v_l = np.log10(v_l)

        mx = max(np.max(t_l), np.max(v_l))
        mn = min(np.min(t_l), np.min(v_l))

        def scale(v):
            return (v - mn) / (mx - mn)

        if t_l is not None:
            self.loss_ax.plot(t_e, scale(t_l) + self.i, 'C0')

        if v_l is not None:
            self.loss_ax.plot(v_e, scale(v_l) + self.i, 'C1')

        if lr_v is not None:
            self.lr_ax.plot(lr_e, np.divide(lr_v, np.max(lr_v)) + self.i, zorder=-10, color='k', ls='--')

        self.plot.axes.text(0, self.i+0.1, expid, ha='left', va='bottom')
        self.i += 1.1

        self.legend()
        self.plot.redraw_and_flush()

    def legend(self):
        self.plot.legend(
            [plt.Line2D([], [], color='C0'), plt.Line2D([], [], color='C1'), plt.Line2D([], [], color='k', ls='--'), ],
            ['training loss', 'validation loss', 'learning rate', ],
        )

