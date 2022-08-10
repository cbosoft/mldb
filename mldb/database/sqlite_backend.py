from sqlite3 import connect
import os

from ..config import CONFIG, SQLiteConfig
from .base import BaseDatabase


CONFIG: SQLiteConfig


class SQLiteDatabase(BaseDatabase):

    COMMAND_SET_STATUS = 'INSERT INTO STATUS (EXPID, STATUS) VALUES (?, ?) ON CONFLICT (EXPID) DO UPDATE SET STATUS=excluded.STATUS;'
    COMMAND_ADD_LOSS = 'INSERT INTO LOSS (EXPID, KIND, EPOCH, VALUE) VALUES (?, ?, ?, ?)'
    COMMAND_ADD_HYPERPARAM = 'INSERT INTO HYPERPARAMS (EXPID, NAME, VALUE) VALUES (?, ?, ?)'
    COMMAND_ADD_METRICS = 'INSERT INTO METRICS (EXPID, KIND, EPOCH, VALUE) VALUES (?, ?, ?, ?);'
    COMMAND_SET_CONFIG = 'INSERT INTO CONFIG (EXPID, CONFIG) VALUES (?, ?);'
    COMMAND_ADD_STATE = 'INSERT INTO STATE (EXPID, EPOCH, PATH) VALUES (?, ?, ?);'
    COMMAND_GET_STATE = 'SELECT PATH FROM STATE WHERE EXPID=? AND EPOCH=?;'

    def __init__(self, root_dir=None):
        super().__init__(os.path.dirname(CONFIG.db_path) if root_dir is None else root_dir)
        self.conn = self.cursor = None
        self.connect()
        self.ensure_schema()

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

    def get_state_file(self, exp_id: str, epoch: int) -> str:
        self.cursor.execute(self.COMMAND_GET_STATE, (exp_id, epoch))
        results = self.cursor.fetchall()
        n_results = len(results)
        assert n_results < 2, f'Too many results returned! (expected 1, got {n_results})'
        assert n_results > 0, f'Too few results returned! (expected 1, got {n_results})'

        state_file = results[0][0]
        return self.desanitise_path(state_file)