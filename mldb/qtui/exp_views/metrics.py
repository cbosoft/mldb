from collections import defaultdict

import scipy.stats
from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem
import numpy as np
from sklearn.manifold import TSNE

from ..db_iop import DBExpMetrics, DBQuery
from ..plot_widget import PlotWidget
from .view_base import BaseExpView


def wrap(s: str) -> str:
    MAX = 75
    s = s.replace('_2018', '').replace('_lim50', '').replace('PolyS,PolyS', 'PolyS')
    if len(s) > MAX:
        # split on ';' before MAX or just at MAX if ';' can't be found.
        pivot = s.rfind(';', 0, MAX) + 1
        if not pivot:
            pivot = MAX
        s = s[:pivot] + '\n' + s[pivot:]
    return s


class MetricsView(BaseExpView):
    GROUP_QUERY = 'SELECT * FROM EXPGROUPS WHERE EXPID=\'{}\';'

    def __init__(self, *expids: str):
        super().__init__(*expids)
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.error_plot = PlotWidget()
        self.error_plot_alt = PlotWidget()
        self.corr_plot = PlotWidget()
        self.tsne_plot = PlotWidget()
        self.tabs.addTab(self.error_plot, 'Errors')
        self.group_parts_selector = QComboBox()
        self.group_parts_set = set()
        self.group_parts_data = dict()
        alt_plot_container = QWidget()
        alt_plot_container.layout = QVBoxLayout(alt_plot_container)
        alt_plot_container.layout.addWidget(self.error_plot_alt)
        alt_plot_container.layout.addWidget(self.group_parts_selector)
        self.tabs.addTab(alt_plot_container, 'Errors (alt)')
        self.tabs.addTab(self.corr_plot, 'Correlations')
        self.metric_table = QTableWidget()
        self.tabs.addTab(self.metric_table, 'Table')

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

            for group in groups:
                parts = group.split(';')
                self.group_parts_data[group] = dict()
                for part in parts:
                    k, v = part.split('=')
                    self.group_parts_set.add(k)

                    try:
                        v = float(v)
                    except:
                        pass

                    self.group_parts_data[group][k] = v

            self.groupings_by_exp[expid] = groups
        except Exception as e:
            print(e)

        self.readiness += 1

        if self.readiness >= 0:
            self.group_parts_selector.addItems(sorted(self.group_parts_set))
            self.group_parts_selector.currentIndexChanged.connect(self.plot_errors)
            self.plot_metrics()

    def plot_metrics(self):
        self.sort_exps_by_group()
        self.plot_errors()
        self.plot_corrs()
        self.plot_tsne(self.errors)
        self.fill_table()

    def fill_table(self):
        self.metric_table.setColumnCount(6)
        self.metric_table.setHorizontalHeaderLabels(['Group', 'Metric', 'Mean', 'Median', 'Min', 'Max'])
        self.metric_table.setRowCount(0)
        r = 0
        for i, (group, expids) in enumerate(sorted(self.exps_by_group.items())):
            values = dict()
            for exp in expids:
                for m, v in self.metrics_by_exp[exp].items():
                    if m not in values:
                        values[m] = []
                    values[m].append(v)

            for m, v in values.items():
                self.metric_table.setRowCount(r + 1)
                self.metric_table.setItem(r, 0, QTableWidgetItem(group))
                self.metric_table.setItem(r, 1, QTableWidgetItem(m))
                self.metric_table.setItem(r, 2, QTableWidgetItem(str(np.mean(v))))
                self.metric_table.setItem(r, 3, QTableWidgetItem(str(np.median(v))))
                self.metric_table.setItem(r, 4, QTableWidgetItem(str(np.max(v))))
                self.metric_table.setItem(r, 5, QTableWidgetItem(str(np.min(v))))
                r += 1

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
        self.plot_metric_set_alt(self.error_plot_alt, sorted(self.errors), self.exps_by_group)

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
                x, y, 'o', color=f'C{i}', label=wrap(group)
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
        plot_widget.axes.set_ylabel('Error')
        plot_widget.legend(loc='lower center', bbox_to_anchor=(0.5, 1.02))
        plot_widget.axes.set_yscale('log')
        plot_widget.redraw_and_flush()

    def plot_metric_set_alt(self, plot_widget: PlotWidget, metrics_set: list, groupings: dict):

        assert groupings, f'Groupings is unset!'

        groups = sorted(groupings)
        n_groups = len(groups)
        n_metrics = len(metrics_set)

        max_exps_per_group = max([len(expids) for expids in groupings.values()])
        print('max exps per group', max_exps_per_group)

        xkey = self.group_parts_selector.currentText()
        print(f'plotting metrics against {xkey}')

        x = []
        x_lbls_pos = []
        for g in groups:
            xi = self.group_parts_data[g][xkey]
            x_lbls_pos.append(xi)
            for _ in range(max_exps_per_group):
                x.append(xi)
        x_lbls = None

        ys = np.full((n_groups*max_exps_per_group, n_metrics), np.nan)

        for i, (group, expids) in enumerate(sorted(groupings.items())):
            for j, exp in enumerate(expids):
                for k, m in enumerate(metrics_set):
                    ys[i*max_exps_per_group + j, k] = self.metrics_by_exp[exp].get(m, float('nan'))

        plot_widget.clear()
        for i, metric in enumerate(metrics_set):
            plot_widget.axes.plot(
                x, ys[:, i], 'o', color=f'C{i}', label=metric
            )
        plot_widget.axes.set_ylabel('Error')
        plot_widget.axes.set_xlabel(xkey)
        plot_widget.axes.set_xticks(
           x, x_lbls,
        )
        plot_widget.legend()
        plot_widget.axes.set_yscale('log')
        plot_widget.redraw_and_flush()

    def plot_tsne(self, metrics_set):
        data, group_idxs = [], []
        for i, (group, expids) in enumerate(self.exps_by_group.items()):
            for expid in expids:
                data.append([
                    self.metrics_by_exp[expid][m]
                    for m in metrics_set
                    if (expid in self.metrics_by_exp) and (m in self.metrics_by_exp[expid])
                ])
                group_idxs.append(i)
        data = np.array(data)
        if len(data) < 2:
            print('Not enough data for TSNE metrics plot')
            return
        groups = list(self.exps_by_group.keys())
        tsne = TSNE(
            perplexity=min(len(data) - 1, 5),
            learning_rate='auto',
            init='pca'
        )
        res = tsne.fit_transform(data)

        x = res[:, 0]
        y = res[:, 1]
        xy_by_group = defaultdict(lambda: ([], []))
        for x, y, i in zip(x, y, group_idxs):
            group = groups[i]
            xy_by_group[group][0].append(x)
            xy_by_group[group][1].append(y)

        for group, (x, y) in xy_by_group.items():
            self.tsne_plot.axes.plot(x, y, 'o', alpha=0.5, label=group)

        self.tsne_plot.axes.set_xlabel('Component 1')
        self.tsne_plot.axes.set_ylabel('Component 2')
        self.tsne_plot.redraw_and_flush()

        tab_names = {self.tabs.tabText(i) for i in range(self.tabs.count())}
        if 'TSNE' not in tab_names:
            self.tabs.addTab(self.tsne_plot, 'TSNE')
