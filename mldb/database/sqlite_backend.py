from sqlite3 import connect
import os
import json

from ..config import CONFIG, SQLiteConfig
from .base import BaseDatabase


CONFIG: SQLiteConfig


class SQLiteDatabase(BaseDatabase):

    COMMAND_SET_STATUS = 'INSERT INTO STATUS (EXPID, STATUS) VALUES (?, ?) ON CONFLICT (EXPID) DO UPDATE SET STATUS=excluded.STATUS;'
    COMMAND_GET_STATUS = 'SELECT * FROM STATUS WHERE EXPID=?;'
    COMMAND_ADD_LOSS = 'INSERT INTO LOSS (EXPID, KIND, EPOCH, VALUE) VALUES (?, ?, ?, ?)'
    COMMAND_GET_LOSSES = 'SELECT * FROM LOSS WHERE EXPID=?;'
    COMMAND_ADD_HYPERPARAM = 'INSERT INTO HYPERPARAMS (EXPID, NAME, VALUE) VALUES (?, ?, ?)'
    COMMAND_GET_HYPERPARAMS = 'SELECT * FROM HYPERPARAMS WHERE EXPID=?;'
    COMMAND_ADD_METRICS = 'INSERT INTO METRICS (EXPID, KIND, EPOCH, VALUE) VALUES (?, ?, ?, ?);'
    COMMAND_GET_LATEST_METRICS = 'SELECT * FROM METRICS WHERE (EXPID, EPOCH) IN (SELECT EXPID, max(EPOCH) FROM METRICS WHERE EXPID=? GROUP BY EXPID);'
    COMMAND_SET_CONFIG = 'INSERT INTO CONFIG (EXPID, CONFIG) VALUES (?, ?);'
    COMMAND_ADD_STATE = 'INSERT INTO STATE (EXPID, EPOCH, PATH) VALUES (?, ?, ?);'
    COMMAND_GET_STATE = 'SELECT PATH FROM STATE WHERE EXPID=? AND EPOCH=?;'
    COMMAND_ADD_LR = 'INSERT INTO LEARNINGRATE (EXPID, EPOCH, VALUE) VALUES (?, ?, ?)'
    COMMAND_GET_LRS = 'SELECT (EPOCH, VALUE) FROM LEARNINGRATE WHERE EXPID=? ORDER BY EPOCH;'
    COMMAND_ADD_QUALRESMETA = 'INSERT INTO QUALITATIVERESULTSMETA (EXPID, PLOTID, VALUE) VALUES (?, ?, ?)'
    COMMAND_ADD_QUALRES = 'INSERT INTO QUALITATIVERESULTS (EXPID, EPOCH, PLOTID, VALUE) VALUES (?, ?, ?, ?)'
    COMMAND_GET_QUALRES = 'SELECT * FROM QUALITATIVERESULTS WHERE EXPID=? AND PLOTID=? ORDER BY EPOCH ASC;'
    COMMAND_GET_QUALRESMETA = 'SELECT * FROM QUALITATIVERESULTSMETA WHERE EXPID=? AND PLOTID=?;'

    def __init__(self, root_dir=None):
        super().__init__(os.path.dirname(CONFIG.db_path) if root_dir is None else root_dir)
        self.conn = self.cursor = None
        self.connect()
        self.ensure_schema()

    def __repr__(self):
        return f'SQLite://{CONFIG.db_path}'

    def connect(self):
        self.conn = connect(CONFIG.db_path)
        self.cursor = self.conn.cursor()

    def ensure_schema(self):
        commands = [
            'CREATE TABLE IF NOT EXISTS \
            STATUS (EXPID TEXT NOT NULL UNIQUE, STATUS TEXT NOT NULL);',

            'CREATE TABLE IF NOT EXISTS \
            CONFIG (EXPID TEXT NOT NULL UNIQUE, CONFIG TEXT NOT NULL);',

            'CREATE TABLE IF NOT EXISTS \
            LOSS (EXPID TEXT NOT NULL, EPOCH INTEGER NOT NULL, KIND TEXT NOT NULL, VALUE REAL NOT NULL,\
            UNIQUE(EXPID, EPOCH, KIND));',

            'CREATE TABLE IF NOT EXISTS \
            METRICS (EXPID TEXT NOT NULL, EPOCH INTEGER NOT NULL, KIND TEXT NOT NULL, VALUE REAL NOT NULL,\
            UNIQUE(EXPID, EPOCH, KIND));',

            'CREATE TABLE IF NOT EXISTS \
            STATE (EXPID TEXT NOT NULL, EPOCH INTEGER NOT NULL, PATH TEXT NOT NULL,\
            UNIQUE(EXPID, EPOCH, PATH));',

            'CREATE TABLE IF NOT EXISTS \
            HYPERPARAMS (EXPID TEXT NOT NULL, NAME TEXT NOT NULL, VALUE TEXT NOT NULL,\
            UNIQUE(EXPID, NAME));',

            'CREATE TABLE IF NOT EXISTS \
            LEARNINGRATE (EXPID TEXT NOT NULL, EPOCH INTEGER NOT NULL, VALUE TEXT NOT NULL,\
            UNIQUE(EXPID, EPOCH));',

            'CREATE TABLE IF NOT EXISTS \
            QUALITATIVERESULTSMETA (EXPID TEXT NOT NULL, PLOTID TEXT NOT NULL, VALUE TEXT NOT NULL,\
            UNIQUE(EXPID, PLOTID));',

            'CREATE TABLE IF NOT EXISTS \
            QUALITATIVERESULTS (EXPID TEXT NOT NULL, EPOCH INTEGER NOT NULL, PLOTID TEXT NOT NULL, VALUE TEXT NOT NULL);',
        ]
        for command in commands:
            self.cursor.execute(command)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def set_exp_status(self, exp_id: str, status: str):
        self.cursor.execute(self.COMMAND_SET_STATUS, (exp_id, status))
        self.conn.commit()

    def add_loss_value(self, exp_id: str, kind: str, epoch: int, value: float):
        self.cursor.execute(self.COMMAND_ADD_LOSS, (exp_id, kind, epoch, value))
        self.conn.commit()

    def add_hyperparam(self, exp_id: str, name: str, value: str):
        self.cursor.execute(self.COMMAND_ADD_HYPERPARAM, (exp_id, name, value))
        self.conn.commit()

    def get_hyperparams(self, exp_id: str) -> dict:
        self.cursor.execute(self.COMMAND_GET_HYPERPARAMS, (exp_id,))
        results = self.cursor.fetchall()

        rv = dict()
        for (_, k, v) in results:
            rv[k] = v
        return rv

    def add_metric_value(self, exp_id: str, kind: str, epoch: int, value: float):
        self.cursor.execute(self.COMMAND_ADD_METRICS, (exp_id, kind, epoch, value))
        self.conn.commit()

    def set_config_file(self, exp_id, config_file_path: str):
        config_file_path = self.sanitise_path(config_file_path)
        self.cursor.execute(self.COMMAND_SET_CONFIG, (exp_id, config_file_path))
        self.conn.commit()

    def add_state_file(self, exp_id: str, epoch: int, path: str, error_on_collision=True):
        path = self.sanitise_path(path)
        try:
            self.cursor.execute(self.COMMAND_ADD_STATE, (exp_id, epoch, path))
            self.conn.commit()
        except Exception as e:
            if error_on_collision:
                raise e
            self.conn.rollback()

    def get_state_file(self, exp_id: str, epoch: int) -> str:
        self.cursor.execute(self.COMMAND_GET_STATE, (exp_id, epoch))
        results = self.cursor.fetchall()
        n_results = len(results)
        assert n_results < 2, f'Too many results returned! (expected 1, got {n_results})'
        assert n_results > 0, f'Too few results returned! (expected 1, got {n_results})'

        state_file = results[0][0]
        return self.desanitise_path(state_file)

    def get_experiment_details(self, exp_id) -> dict:
        self.cursor.execute(self.COMMAND_GET_STATUS, (exp_id,))
        results = self.cursor.fetchall()

        if not results:
            return dict(error=True, why='No results returned.')
        elif len(results) > 1:
            return dict(error=True, why='More results than expected.')

        status = results[0][1]

        self.cursor.execute(self.COMMAND_GET_LOSSES, (exp_id,))
        results = self.cursor.fetchall()

        if results:
            res_by_cols = list(zip(*results))

            epochs = res_by_cols[1]
            loss_kinds = res_by_cols[2]
            losses = res_by_cols[3]
            uniq_kinds = set(loss_kinds)
            losses = {
                k: dict(
                    loss=[l for l, lk in zip(losses, loss_kinds) if lk == k],
                    epoch=[e for e, lk in zip(epochs, loss_kinds) if lk == k],
                )
                for k in uniq_kinds
            }
        else:
            losses = dict()

        lr_es, lrs = [], []
        for lr in self.get_lr_values(exp_id):
            e, lr = lr[0][1:-1].split(',')
            lr_es.append(int(e))
            lrs.append(float(lr))

        return dict(
            expid=exp_id,
            status=status,
            losses=losses,
            lrs=dict(epochs=lr_es, lrs=lrs)
        )

    def get_latest_metrics(self, exp_id) -> dict:
        self.cursor.execute(self.COMMAND_GET_LATEST_METRICS, (exp_id,))
        results = self.cursor.fetchall()

        if not results:
            return dict()

        return dict(
            expid=exp_id,
            epoch=results[0][1],
            data={kind: value for _, __, kind, value in results}
        )

    def add_lr_value(self, exp_id: str, epoch: int, value: float):
        self.cursor.execute(self.COMMAND_ADD_LR, (exp_id, epoch, value))
        self.conn.commit()

    def get_lr_values(self, exp_id: str):
        self.cursor.execute(self.COMMAND_GET_LRS, (exp_id,))
        return self.cursor.fetchall()

    def add_qualitative_metadata_json(self, exp_id: str, plot_id: str, value: str):
        self.cursor.execute(self.COMMAND_ADD_QUALRESMETA, (exp_id, plot_id, value))
        self.conn.commit()

    def add_qualitative_result_json(self, exp_id: str, epoch: int, plot_id: str, value: str):
        self.cursor.execute(self.COMMAND_ADD_QUALRES, (exp_id, epoch, plot_id, value))
        self.conn.commit()

    def get_qualitative_result(self, exp_id: str, plot_id: str):
        self.cursor.execute(self.COMMAND_GET_QUALRESMETA, (exp_id, plot_id))
        meta_enc = self.cursor.fetchall()

        qualres = json.loads(meta_enc[0][-1])

        self.cursor.execute(self.COMMAND_GET_QUALRES, (exp_id, plot_id))
        data = self.cursor.fetchall()

        qualres['data'] = []
        for row in data:
            # columns = ['expid', 'epoch', 'plotid', 'value']
            qualres['data'].append(dict(epoch=int(row[1]), **json.loads(row[-1])))

        return qualres
