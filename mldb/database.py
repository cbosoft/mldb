from sqlite3 import connect

from .config import CONFIG


class Database:

    def __init__(self):
        self.path = CONFIG.db_path
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

    def add_metric_value(self, exp_id: str, kind: str, epoch: int, value: float):
        self.cursor.execute(
            'INSERT INTO METRICS (EXPID, KIND, EPOCH, VALUE) VALUES (?, ?, ?, ?);',
            (exp_id, kind, epoch, value)
        )
        self.conn.commit()

    def set_config_file(self, exp_id, config_file_path: str):
        self.cursor.execute('INSERT INTO CONFIG (EXPID, CONFIG);', (exp_id, config_file_path))
        self.conn.commit()

    def add_state_file(self, exp_id: str, epoch: int, path: str):
        self.cursor.execute(
            'INSERT INTO STATE (EXPID, EPOCH, PATH) VALUES (?, ?, ?);', (exp_id, epoch, path)
        )
        self.conn.commit()
