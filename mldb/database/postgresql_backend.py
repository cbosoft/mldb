from ..config import CONFIG, PostgreSQLConfig
from .sqlite_backend import SQLiteDatabase

from psycopg2 import connect

CONFIG: PostgreSQLConfig


class PostgreSQLDatabase(SQLiteDatabase):

    COMMAND_SET_STATUS = 'INSERT INTO STATUS (EXPID, STATUS) VALUES (%s, %s) ON CONFLICT (EXPID) DO UPDATE SET STATUS=excluded.STATUS;'
    COMMAND_GET_STATUS = 'SELECT * FROM STATUS WHERE EXPID=%s;'
    COMMAND_ADD_LOSS = 'INSERT INTO LOSS (EXPID, KIND, EPOCH, VALUE) VALUES (%s, %s, %s, %s)'
    COMMAND_GET_LOSSES = 'SELECT * FROM LOSS WHERE EXPID=%s;'
    COMMAND_ADD_HYPERPARAM = 'INSERT INTO HYPERPARAMS (EXPID, NAME, VALUE) VALUES (%s, %s, %s)'
    COMMAND_GET_HYPERPARAMS = 'SELECT * FROM HYPERPARAMS WHERE EXPID=%s;'
    COMMAND_ADD_METRICS = 'INSERT INTO METRICS (EXPID, KIND, EPOCH, VALUE) VALUES (%s, %s, %s, %s);'
    COMMAND_GET_LATEST_METRICS = 'SELECT * FROM METRICS WHERE (EXPID, EPOCH) IN (SELECT EXPID, max(EPOCH) FROM METRICS WHERE EXPID=%s GROUP BY EXPID);'
    COMMAND_SET_CONFIG = 'INSERT INTO CONFIG (EXPID, CONFIG) VALUES (%s, %s);'
    COMMAND_ADD_STATE = 'INSERT INTO STATE (EXPID, EPOCH, PATH) VALUES (%s, %s, %s);'
    COMMAND_GET_STATE = 'SELECT PATH FROM STATE WHERE EXPID=? AND EPOCH=%s;'
    COMMAND_GET_EXPERIMENT_DETAILS = 'SELECT * FROM STATUS INNER JOIN LOSS ON status.expid=loss.expid WHERE status.expid=%s;'

    def __init__(self):
        super().__init__(CONFIG.root_dir)

        self.host = CONFIG.host
        self.user = CONFIG.user
        self.port = CONFIG.port
        self.database = CONFIG.database

    def connect(self):
        self.conn = connect(**CONFIG.as_dict())
        self.cursor = self.conn.cursor()

    def __repr__(self):
        return f'PostgreSQL://{self.user}@{self.host}:{self.port}/{self.database}'
