from typing import Set, Optional

import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton
from PySide6.QtCore import Signal
from mldb import Database
from sklearn.manifold import TSNE
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

from .db_iop import DBQuery
from .plot_widget import PlotWidget
from .util import FuncRunner


class ModelListWidget(QWidget):

    status_signal = Signal(str)
    progress_signal = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QVBoxLayout(self)

        self.model_selector = QComboBox()
        self.layout.addWidget(self.model_selector)

        self.tSNE_button = QPushButton('t-SNE plot')
        self.layout.addWidget(self.tSNE_button)
        self.tSNE_button.clicked.connect(self.do_tSNE)

        self.plot = PlotWidget(ax_rect=(0.15, 0.15, 0.8, 0.8))
        self.layout.addWidget(self.plot)

        self.models: Optional[Set[str]] = None
        self.tSNE_data = None

        query = DBQuery('SELECT * FROM STATUS;')
        query.results_returned.connect(self.populate_models)
        query.start()

    def populate_models(self, rows):
        assert self.models is None
        self.models = set()
        for expid, _ in rows:
            model_name = (expid
                          .replace('_', '')
                          .replace('-', '')
                          .replace('fold', '')
                          .strip('0123456789'))
            self.models.add(model_name)

        for model in self.models:
            self.model_selector.addItem(f'Model {model}', userData=model)

    def do_tSNE(self):
        FuncRunner(self.do_tSNE_worker).start()

    def do_tSNE_worker(self):
        model = self.model_selector.currentData()

        self.set_progress(0)
        self.plot.clear()
        with Database() as db:
            db.cursor.execute(f'SELECT * FROM STATUS WHERE EXPID LIKE \'%%{model}%%\';')
            rows = db.cursor.fetchall()
            self.set_progress(10)

            data = []
            for expid, status in rows:
                datum = {}
                hparams = db.get_hyperparams(expid)
                if hparams and 'error' not in hparams:
                    datum.update(hparams)
                metrics = db.get_latest_metrics(expid)
                if metrics and 'error' not in metrics:
                    datum.update(metrics['data'])
                # datum['expid'] = expid  # dunno if I want to include this?
                datum['status'] = status
                data.append(datum)

        self.set_progress(50)
        all_keys = set(data[0])
        for datum in data:
            all_keys.update(datum)
        all_keys = list(all_keys)
        data_arr = np.zeros((len(data), len(all_keys)), dtype=str)
        for i, datum in enumerate(data):
            for j, k in enumerate(all_keys):
                if k in datum:
                    data_arr[i, j] = datum[k]
        self.set_progress(75)
        data_enc = np.zeros(data_arr.shape, dtype=int)
        for j, col in enumerate(data_arr.transpose()):
            uniq_col = np.unique(col)
            v2idx = {v: i+1 for i, v in enumerate(uniq_col)}
            for i, v in enumerate(data_arr[:, j]):
                data_enc[i, j] = v2idx[v]

        tsne = TSNE(
            perplexity=min(len(data_enc)-1, 5),
            learning_rate='auto',
            init='pca'
        )
        res = tsne.fit_transform(data_enc)

        print(tsne.get_params())

        self.set_progress(95)
        self.set_progress(101)

        self.tSNE_data = dict(
            x=res[:, 0],
            y=res[:, 1],
            colour=0,
            data_enc=data_enc,
            keys=sorted(all_keys)
        )
        self.plot_tSNE()

    def plot_tSNE(self):
        assert self.tSNE_data is not None
        data_enc = self.tSNE_data['data_enc']
        colour_i = self.tSNE_data['colour']
        x = self.tSNE_data['x']
        y = self.tSNE_data['y']
        keys = self.tSNE_data['keys']
        colour_data = data_enc[:, colour_i]
        print('colour_by', keys[colour_i])
        smap = ScalarMappable(norm=Normalize(vmin=0, vmax=colour_data.max()), cmap='viridis')
        for x, y, c in zip(x, y, colour_data):
            colour = smap.to_rgba(c)
            self.plot.axes.plot([x], [y], 'o', color=colour)
        self.plot.axes.set_xlabel('Component 1')
        self.plot.axes.set_ylabel('Component 2')
        self.plot.redraw_and_flush()

    def set_status(self, s: str):
        self.status_signal.emit(s)

    def set_progress(self, p: int):
        self.progress_signal.emit(p)
