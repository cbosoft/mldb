import numpy as np
from PySide6.QtWidgets import QHBoxLayout, QTabWidget

from ..plot_widget import PlotWidget
from ..db_iop import DBExpQualResults
from .view_base import BaseExpView


class ExpQualresView(BaseExpView):
    def __init__(self, *expids):
        if len(expids) > 1:
            print(
                "Too many experiments selected: only showing qualitative results for one (1) experiment."
            )
            expids = expids[:1]
        super().__init__(*expids)

        self.plotids_and_qualres = None
        self.expid = expids[0]
        self.layout = QHBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        self.refresh()

    def refresh(self):
        DBExpQualResults(self.expid, self.qualres_returned).start()

    def qualres_returned(self, plotids_and_qualres):
        self.replot(plotids_and_qualres)

    def replot(self, plotids_and_qualres=None):
        if plotids_and_qualres is not None:
            self.plotids_and_qualres = plotids_and_qualres
        else:
            plotids_and_qualres = self.plotids_and_qualres

        for plotid, data in plotids_and_qualres:
            pw = PlotWidget()
            pw.plotid = plotid
            self.tabs.addTab(pw, plotid)
            self.plot_qualres(pw, **data)
            pw.redraw_and_flush()

    def plot_qualres(self, plotwidget: PlotWidget, *, kind: str, **data):
        if kind == "vector":
            self.plot_vector(plotwidget, **data)
        elif kind == "guess":
            if isinstance(data["data"][0]["output"], float):
                self.plot_scalar(plotwidget, **data)
            elif len(data["data"][0]["output"]) > 1:
                self.plot_vector(plotwidget, **data)
            elif len(np.array(data["data"][0]["output"]).flatten()) > 1:
                nplots = len(np.array(data["data"][0]["output"]).flatten())
                try:
                    plotids, tag = plotwidget.plotid.split(";")
                    plotids = plotids.split("-")
                    plotids = [(pid + ";" + tag) for pid in plotids]
                    assert len(plotids) == nplots
                except (IndexError, AssertionError, ValueError):
                    plotids = [f"{plotwidget.plotid}{i}" for i in range(nplots)]
                self.tabs.removeTab(self.tabs.indexOf(plotwidget))
                for i, plotid in enumerate(plotids):
                    pw = PlotWidget()
                    pw.plotid = plotid
                    self.plot_scalar(pw, indx=i, **data)
                    self.tabs.addTab(pw, plotid)
            else:
                self.plot_scalar(plotwidget, **data)
        else:
            raise NotImplementedError(f'plot kind not yet supported: "{kind}"')

    @staticmethod
    def plot_vector(
        plot: PlotWidget,
        *,
        xlabel: str,
        ylabel: str,
        xscale="linear",
        yscale="linear",
        data: list,
    ):
        plot.axes.set_xlabel(xlabel)
        plot.axes.set_ylabel(ylabel)
        plot.axes.set_xscale(xscale)
        plot.axes.set_yscale(yscale)

        # TODO:
        #  - Colour by epoch?
        #  - Colour by GT/class?

        last_epoch = max([d["epoch"] for d in data])
        data = [d for d in data if d["epoch"] == last_epoch]

        for i, datum in enumerate(data):
            colour = f"C{i%10}"
            datum: dict
            if "x" not in datum:
                x = np.geomspace(1, 1e3, 100)
            else:
                x = datum["x"]

            plot.plot(x, datum["output"], "-", color=colour)
            if "target" in datum:
                plot.plot(x, datum["target"], "--", color=colour)
