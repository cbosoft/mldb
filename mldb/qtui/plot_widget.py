import matplotlib

matplotlib.use("Qt5Agg")

from matplotlib import pyplot as plt

from matplotlib.collections import PolyCollection
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from PySide6 import QtCore

from .util import is_dark_theme

if is_dark_theme():
    plt.style.use("dark_background")


class PlotWidget(FigureCanvasQTAgg):
    selection_changed = QtCore.Signal(float, float, bool, name="selection_changed")

    def __init__(self, dpi=100, can_select=False, ax_rect=(0.2, 0.2, 0.75, 0.7)):
        fig = Figure(dpi=dpi)
        fig.set_tight_layout(True)
        super().__init__(fig)
        self.axes: Axes = fig.add_subplot()
        self._twax = None

        self.selection_axes = [0, 0]
        self.selection_data = [0, 0]

        self.can_select = can_select
        self.is_selecting = False
        selector_kws = dict(color="k", alpha=0.1, transform=self.axes.transAxes)
        self.selection_left: PolyCollection = self.axes.fill_betweenx(
            [-2.0, 2.0], -2.0, -2.0, **selector_kws
        )
        self.selection_right: PolyCollection = self.axes.fill_betweenx(
            [-2.0, 2.0], 2.0, 2.0, **selector_kws
        )

    @property
    def twax(self):
        if self._twax is None:
            self._twax = self.axes.twinx()
        return self._twax

    def plot(self, *args, **kwargs):
        rv = self.axes.plot(*args, **kwargs)
        return rv

    def legend(self, *args, **kwargs):
        self.axes.legend(*args, **kwargs)

    def redraw_and_flush(self):
        self.axes.relim()
        self.axes.autoscale()
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def clear_axes(self):
        for a in self.axes.get_lines():
            a.remove()

    def clear_twax(self):
        if self._twax:
            for a in self._twax.get_lines():
                a.remove()

    def clear(self):
        self.clear_axes()
        self.clear_twax()

    def convert_pt(self, pt: QtCore.QPoint):
        w, h = self.get_width_height()
        pw, ph = self.get_width_height(physical=True)
        s = pw / w
        pt = pt.x() * s, (h - pt.y()) * s
        pt_data = self.axes.transData.inverted().transform_point(pt)
        pt_axes = self.axes.transAxes.inverted().transform_point(pt)
        return pt_data, pt_axes

    def mouseMoveEvent(self, event):
        if self.is_selecting and self.can_select:
            pt_data, pt_axes = self.convert_pt(event.pos())
            self.selection_data[1] = pt_data[0]
            self.selection_axes[1] = pt_axes[0]
            self.update_selection()

    def mousePressEvent(self, event):
        if self.can_select:
            self.is_selecting = True
            pt_data, pt_axes = self.convert_pt(event.pos())
            self.selection_data[0] = self.selection_data[1] = pt_data[0]
            self.selection_axes[0] = self.selection_axes[1] = pt_axes[0]
            self.update_selection()

    def mouseReleaseEvent(self, event):
        if self.can_select:
            self.is_selecting = False
            self.update_selection()

    def set_selection(self, lb_data, ub_data):
        lb_px = self.axes.transData.transform_point((lb_data, 0))[0]
        lb_axes = self.axes.transAxes.inverted().transform_point((lb_px, 0))[0]
        ub_px = self.axes.transData.transform_point((ub_data, 0))[0]
        ub_axes = self.axes.transAxes.inverted().transform_point((ub_px, 0))[0]

        self.selection_axes = sorted((lb_axes, ub_axes))
        self.selection_data = sorted((lb_data, ub_data))
        self.update_selection()

    def update_selection(self):
        sleft, sright = sorted(self.selection_axes)
        if sleft == sright:
            sleft = -2.0
            sright = 2.0
            has_selection = False
        else:
            has_selection = True
        left = self.selection_left.get_paths()[0]
        left.vertices[0, 0] = left.vertices[3:, 0] = sleft

        right = self.selection_right.get_paths()[0]
        right.vertices[0, 0] = right.vertices[3:, 0] = sright

        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        self.selection_changed.emit(*sorted(self.selection_data), has_selection)
