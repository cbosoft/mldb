from collections import defaultdict

import scipy.stats
from PySide6.QtWidgets import QTabWidget, QHBoxLayout
import numpy as np

from ..db_iop import DBExpMetrics, DBQuery
from ..plot_widget import PlotWidget
from .view_base import BaseExpView


class MetricsView(BaseExpView):

    GROUP_QUERY = 'SELECT * FROM EXPGROUPS WHERE EXPID=\'{}\';'

    def __init__(self, *expids: str):
        super().__init__(*expids)
        self.layout = QHBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.error_plot = PlotWidget()
        self.corr_plot = PlotWidget()
        self.tabs.addTab(self.error_plot, 'Errors')
        self.tabs.addTab(self.corr_plot, 'Correlations')

        self.errors = set()
        self.corrs = set()
        self.metrics_by_exp = dict()
        self.groupings_by_exp = {e: [] for e in self.expids}
        self.exps_by_group = {}
        self.readiness = 0

        self.refresh()

    def refresh(self):
        self.readiness = -len(self.expids)
        for expid in self.expids:
            DBExpMetrics(
                expid,
                self.metrics_returned
            ).start()

    def metrics_returned(self, d):
        if not d:
            self.readiness += 1
            return

        expid = d['expid']

        for m, _ in d['data'].items():
            lowercase_m = m.lower()
            # if 'error' in the name (or MSE, RMSE), then the metric is an error value.
            # otherwise, it must be a correlation value.
            if 'error' in lowercase_m or 'mse' in lowercase_m:
                self.errors.add(m)
            else:
                self.corrs.add(m)

        self.metrics_by_exp[expid] = d['data']
        DBQuery(self.GROUP_QUERY.format(expid), self.grouping_returned).start()

    def grouping_returned(self, rows):
        try:
            expid = rows[0][0]
            groups = [row[1] for row in rows]

            self.groupings_by_exp[expid] = groups
        except Exception as e:
            print(e)

        self.readiness += 1

        if self.readiness >= 0:
            self.plot_metrics()

    def plot_metrics(self):
        self.sort_exps_by_group()
        self.plot_errors()
        self.plot_corrs()

    def sort_exps_by_group(self):
        self.exps_by_group = defaultdict(list)
        for exp, groups in self.groupings_by_exp.items():
            ng = len(groups)

            if not ng:
                print(f'no groups for {exp}')
                if not self.groupings_by_exp:
                    self.exps_by_group[exp].append(exp)
            else:
                if ng > 1:
                    print(f'experiment {exp} has many groups; choosing first ({groups[0]})')
                self.exps_by_group[groups[0]].append(exp)

    def plot_errors(self):
        self.plot_metric_set(self.error_plot, sorted(self.errors), self.exps_by_group)

    def plot_corrs(self):
        self.plot_metric_set(self.corr_plot, sorted(self.corrs), self.exps_by_group)

    def plot_metric_set(self, plot_widget: PlotWidget, metrics_set: list, groupings: dict):

        assert groupings, f'Groupings is unset!'

        # table.clear()
        # table.setColumnCount(2)
        # table.setRowCount((len(self.expids)+1)*len(self.low_metrics))
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
        for i, (group, expids) in enumerate(sorted(groupings.items())):
            x, y = [], []
            for exp in expids:
                for j, m in enumerate(metrics_set):
                    x.append(j)
                    y.append(self.metrics_by_exp[exp].get(m, float('nan')))
            plot_widget.axes.plot(
                x, y, 'o', color=f'C{i}', label=group
            )
            edges = np.arange(len(metrics_set)+1) - 0.5
            x_means = np.arange(len(metrics_set))
            y_means = scipy.stats.binned_statistic(x, y, bins=edges)[0]
            for xi, yi in zip(x_means, y_means):
                xi = np.add([-0.2, 0.2], xi)
                yi = [yi, yi]
                plot_widget.axes.plot(
                    xi, yi, '--', color=f'C{i}'
                )
        lbl_x = np.arange(len(metrics_set))
        plot_widget.axes.set_xticks(
            lbl_x, labels,
        )
        plot_widget.legend()
        plot_widget.axes.set_yscale('log')
        plot_widget.redraw_and_flush()
