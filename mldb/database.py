from sqlite3 import connect
import os

from .config import CONFIG


class Database:

    def __init__(self):
        self.path = CONFIG.db_path
        self.dir_path = os.path.dirname(self.path)
        self.conn = connect(self.path)
        self.cursor = self.conn.cursor()
        self.ensure_schema()

    def ensure_schema(self):
        commands = [
            'CREATE TABLE IF NOT EXISTS \
            "STATUS" ("EXPID" TEXT NOT NULL UNIQUE, "STATUS" TEXT NOT NULL);',

            'CREATE TABLE IF NOT EXISTS \
            "CONFIG" ("EXPID" TEXT NOT NULL UNIQUE, "CONFIG" TEXT NOT NULL);',

            'CREATE TABLE IF NOT EXISTS \
            "LOSS" ("EXPID" TEXT NOT NULL, "EPOCH" INTEGER NOT NULL, "KIND" TEXT NOT NULL, "VALUE" REAL NOT NULL,\
            UNIQUE(EXPID, EPOCH, KIND));',

            'CREATE TABLE IF NOT EXISTS \
            "METRICS" ("EXPID" TEXT NOT NULL, "EPOCH" INTEGER NOT NULL, "KIND" TEXT NOT NULL, "VALUE" REAL NOT NULL,\
            UNIQUE(EXPID, EPOCH, KIND));',

            'CREATE TABLE IF NOT EXISTS \
            "STATE" ("EXPID" TEXT NOT NULL, "EPOCH" INTEGER NOT NULL, "PATH" TEXT NOT NULL,\
            UNIQUE(EXPID, EPOCH, PATH));',

            'CREATE TABLE IF NOT EXISTS \
            "HYPERPARAMS" ("EXPID" TEXT NOT NULL, "NAME" TEXT NOT NULL, "VALUE" TEXT NOT NULL,\
            UNIQUE(EXPID, NAME));',
        ]
        for command in commands:
            self.cursor.execute(command)
        self.conn.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def set_exp_status(self, exp_id: str, status: str):
        self.cursor.execute(
            'INSERT INTO STATUS (EXPID, STATUS) VALUES (?, ?) ON CONFLICT (EXPID) DO UPDATE SET STATUS=excluded.STATUS;',
            (exp_id, status)
        )
        self.conn.commit()

    def add_loss_value(self, exp_id: str, kind: str, epoch: int, value: float):
        self.cursor.execute(
            'INSERT INTO LOSS (EXPID, KIND, EPOCH, VALUE) VALUES (?, ?, ?, ?)',
            (exp_id, kind, epoch, value))
        self.conn.commit()

    def add_hyperparam(self, exp_id: str, name: str, value: str):
        self.cursor.execute(
            'INSERT INTO HYPERPARAMS (EXPID, NAME, VALUE) VALUES (?, ?, ?)',
            (exp_id, name, value))
        self.conn.commit()

    def add_metric_value(self, exp_id: str, kind: str, epoch: int, value: float):
        self.cursor.execute(
            'INSERT INTO METRICS (EXPID, KIND, EPOCH, VALUE) VALUES (?, ?, ?, ?);',
            (exp_id, kind, epoch, value)
        )
        self.conn.commit()

    def set_config_file(self, exp_id, config_file_path: str):
        config_file_path = os.path.relpath(config_file_path, self.dir_path)
        self.cursor.execute('INSERT INTO CONFIG (EXPID, CONFIG) VALUES (?, ?);', (exp_id, config_file_path))
        self.conn.commit()

    def add_state_file(self, exp_id: str, epoch: int, path: str, error_on_collision=True):
        path = os.path.relpath(path, self.dir_path)
        try:
            self.cursor.execute(
                'INSERT INTO STATE (EXPID, EPOCH, PATH) VALUES (?, ?, ?);', (exp_id, epoch, path)
            )
            self.conn.commit()
        except Exception as e:
            if error_on_collision:
                raise e

    def get_state_file(self, exp_id: str, epoch: int) -> str:
        self.cursor.execute(
            'SELECT PATH FROM STATE WHERE EXPID=? AND EPOCH=?;', (exp_id, epoch)
        )
        results = self.cursor.fetchall()
        n_results = len(results)
        assert n_results < 2, f'Too many results returned! (expected 1, got {n_results})'
        assert n_results > 0, f'Too few results returned! (expected 1, got {n_results})'

        state_file = results[0][0]
        # State file path is relative to the db location, make it absolute.
        return os.path.join(
            self.dir_path,
            state_file
        )
