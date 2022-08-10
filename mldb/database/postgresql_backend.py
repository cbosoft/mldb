from ..config import CONFIG, PostgreSQLConfig
from .sqlite_backend import SQLiteDatabase

from psycopg2 import connect

CONFIG: PostgreSQLConfig


class PostgreSQLDatabase(SQLiteDatabase):

    COMMAND_SET_STATUS = 'INSERT INTO STATUS (EXPID, STATUS) VALUES (%s, %s) ON CONFLICT (EXPID) DO UPDATE SET STATUS=excluded.STATUS;'
    COMMAND_ADD_LOSS = 'INSERT INTO LOSS (EXPID, KIND, EPOCH, VALUE) VALUES (%s, %s, %s, %s)'
    COMMAND_ADD_HYPERPARAM = 'INSERT INTO HYPERPARAMS (EXPID, NAME, VALUE) VALUES (%s, %s, %s)'
    COMMAND_ADD_METRICS = 'INSERT INTO METRICS (EXPID, KIND, EPOCH, VALUE) VALUES (%s, %s, %s, %s);'
    COMMAND_SET_CONFIG = 'INSERT INTO CONFIG (EXPID, CONFIG) VALUES (%s, %s);'
    COMMAND_ADD_STATE = 'INSERT INTO STATE (EXPID, EPOCH, PATH) VALUES (%s, %s, %s);'
    COMMAND_GET_STATE = 'SELECT PATH FROM STATE WHERE EXPID=? AND EPOCH=%s;'

    def __init__(self):
        super().__init__(CONFIG.root_dir)

        self.host = CONFIG.host
        self.user = CONFIG.user
        self.port = CONFIG.port

    def connect(self):
        self.conn = connect(**CONFIG.as_dict())
        self.cursor = self.conn.cursor()

    def __repr__(self):
        return f'PostgreSQL://{self.user}@{self.host}:{self.port}'
