import matplotlib.pyplot as plt
from PySide6.QtWidgets import QHBoxLayout
import numpy as np

from ..plot_widget import PlotWidget
from ..db_iop import DBExpDetails
from .view_base import BaseExpView


class ExpLossAndLRView(BaseExpView):
    def __init__(self, *expids: str):
        if len(expids) > 4:
            print("Too many experiments for plotting losses; only showing first three.")
            expids = expids[:4]
        super().__init__(*expids)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # plot of loss against epoch, with secondary axis showing learning rate.
        self.plot = PlotWidget(ax_rect=(0.2, 0.2, 0.6, 0.7))
        self.loss_ax = self.plot.axes
        self.loss_ax.set_yticks([])
        self.loss_ax.set_title("Loss v Epoch")
        self.loss_ax.set_xlabel("Epoch [#]")
        self.loss_ax.set_ylabel("Loss [AU]")
        self.lr_ax = self.plot.axes.twinx()
        self.lr_ax.set_ylabel("Learning rate")
        self.layout.addWidget(self.plot)

        self.refresh()
        self.i = 0.0

    def refresh(self):
        self.plot.clear()
        self.i = 0.0
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

        self.update_plots(
            expid,
            train_epochs,
            train_losses,
            valid_epochs,
            valid_losses,
            lr_epochs,
            lr_values,
        )

    def update_plots(self, expid, t_e, t_l, v_e, v_l, lr_e, lr_v):

        if self.i > 0:
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
                slt_l[-1] + self.i + 0.1,
                f"{t_l[-1]:.2e}",
                ha="right",
                va="bottom",
                color="C0",
            )

        if v_l is not None:
            slv_l = scale(lv_l)
            self.loss_ax.plot(v_e, slv_l + self.i, "C1")
            self.loss_ax.text(
                t_e[-1],
                slv_l[-1] + self.i + 0.1,
                f"{v_l[-1]:.2e}",
                ha="right",
                va="bottom",
                color="C1",
            )

        if lr_v is not None:
            self.lr_ax.plot(
                lr_e,
                np.divide(lr_v, np.max(lr_v)) + self.i,
                zorder=-10,
                color="k",
                ls="--",
            )

        self.plot.axes.text(0, self.i + 0.1, expid, ha="left", va="bottom")
        self.i += 1.1

        self.legend()
        self.plot.redraw_and_flush()

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
