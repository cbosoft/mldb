import matplotlib.pyplot as plt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QCheckBox,
    QWidget,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt
import numpy as np

from ..plot_widget import PlotWidget
from ..db_iop import DBExpDetails
from ..util import is_dark_theme
from .view_base import BaseExpView


class ExpLossAndLRView(BaseExpView):
    def __init__(self, *expids: str):
        super().__init__(*expids)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        expselector_par = QScrollArea()
        expselector_par.setMaximumWidth(300)
        expselector = QWidget()
        expselector.layout = QVBoxLayout(expselector)
        expselector_par.setWidget(expselector)
        expselector_par.setWidgetResizable(True)
        expselector.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.layout.addWidget(expselector_par)
        self.exp_shown = {}
        self.data_by_exp = {}
        for i, expid in enumerate(expids):
            chk = QCheckBox(expid)
            shown = i < 3
            chk.setCheckState(
                Qt.CheckState.Checked if shown else Qt.CheckState.Unchecked
            )
            self.exp_shown[expid] = shown

            def lwi_checked(v, *, e=expid):
                self.exp_shown[e] = v
                self.replot()

            chk.stateChanged.connect(lwi_checked)
            expselector.layout.addWidget(chk)

        # plot of loss against epoch, with secondary axis showing learning rate.
        self.plot = PlotWidget()
        self.loss_ax = self.plot.axes
        self.lr_ax = self.plot.twax
        self.layout.addWidget(self.plot)

        self.refresh()
        self.i = 0

    def refresh(self):
        self.plot.clear()
        self.i = 0
        for expid in self.expids:
            DBExpDetails(expid, self.details_returned).start()

    def details_returned(self, d: dict):

        expid = d["expid"]

        try:
            train_losses = d["losses"]["train"]["loss"]
            train_epochs = d["losses"]["train"]["epoch"]
        except KeyError:
            print(f"No training losses for {expid}")
            train_losses = None
            train_epochs = None

        try:
            valid_losses = d["losses"]["valid"]["loss"]
            valid_epochs = d["losses"]["valid"]["epoch"]
        except KeyError:
            print(f"No validation losses for {expid}")
            valid_losses = None
            valid_epochs = None

        try:
            lr_epochs = d["lrs"]["epochs"]
            lr_values = d["lrs"]["lrs"]
        except KeyError:
            print(f"No learning rate info for {expid}")
            lr_epochs = None
            lr_values = None

        self.data_by_exp[expid] = dict(
            expid=expid,
            t_e=train_epochs,
            t_l=train_losses,
            v_e=valid_epochs,
            v_l=valid_losses,
            lr_e=lr_epochs,
            lr_v=lr_values,
        )

        self.i += 1

        if self.i == len(self.expids):
            self.replot()

    def replot(self):
        self.i = 0.0
        self.plot.clear()
        for expid, data in self.data_by_exp.items():
            if self.exp_shown[expid]:
                self.update_plots(**data)

        self.loss_ax.set_yticks([])
        self.loss_ax.set_title("Loss v Epoch")
        self.loss_ax.set_xlabel("Epoch [#]")
        self.lr_ax.set_yticks([])
        self.legend()
        self.plot.redraw_and_flush()

    def update_plots(self, expid, t_e, t_l, v_e, v_l, lr_e, lr_v):

        if self.i > 0.0:
            self.loss_ax.axhline(self.i, color="k", alpha=0.2)

        mx, mn = -100, 100
        if t_l is not None:
            lt_l = np.log10(t_l)
            mx = lt_l.max()
            mn = lt_l.min()

        if v_l is not None:
            lv_l = np.log10(v_l)
            mx = max(mx, lv_l.max())
            mn = min(mn, lv_l.min())

        def scale(v):
            return (v - mn) / (mx - mn)

        if t_l is not None:
            slt_l = scale(lt_l)
            self.loss_ax.plot(t_e, slt_l + self.i, "C0")
            self.loss_ax.text(
                t_e[-1],
                self.i + 0.1,
                f"{t_l[-1]:.2e}",
                ha="left",
                va="bottom",
                color="C0",
            )

        if v_l is not None:
            slv_l = scale(lv_l)
            self.loss_ax.plot(v_e, slv_l + self.i, "C1")
            self.loss_ax.text(
                t_e[-1],
                self.i + 0.6,
                f"{v_l[-1]:.2e}",
                ha="left",
                va="bottom",
                color="C1",
            )

        if lr_v is not None and len(lr_v) > 0:
            self.lr_ax.plot(
                lr_e,
                np.divide(lr_v, np.max(lr_v)) + self.i,
                zorder=-10,
                color="0.9" if is_dark_theme() else "k",
                ls="--",
            )

        self.plot.axes.text(0, self.i + 0.1, expid, ha="left", va="bottom")
        self.i += 1.1

    def legend(self):
        self.plot.legend(
            [
                plt.Line2D([], [], color="C0"),
                plt.Line2D([], [], color="C1"),
                plt.Line2D([], [], color="k", ls="--"),
            ],
            [
                "training loss",
                "validation loss",
                "learning rate",
            ],
        )
