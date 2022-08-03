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
