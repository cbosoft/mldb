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
            'CREATE TABLE IF NOT EXISTS "STATUS" ("EXPID" TEXT NOT NULL, "STATUS" TEXT NOT NULL);',

            # Experiment config
            'CREATE TABLE IF NOT EXISTS "CONFIG" ("EXPID" TEXT NOT NULL, "CONFIG" TEXT NOT NULL);',
            
            # losses
            'CREATE TABLE IF NOT EXISTS "LOSS_EPOCH_TRAIN" ("EXPID" TEXT NOT NULL, "EPOCH" INTEGER NOT NULL, "VALUE" REAL NOT NULL);',
            'CREATE TABLE IF NOT EXISTS "LOSS_BATCH_TRAIN" ("EXPID" TEXT NOT NULL, "BATCH" INTEGER NOT NULL, "VALUE" REAL NOT NULL);',
            'CREATE TABLE IF NOT EXISTS "LOSS_EPOCH_VALID" ("EXPID" TEXT NOT NULL, "EPOCH" INTEGER NOT NULL, "VALUE" REAL NOT NULL);',
            'CREATE TABLE IF NOT EXISTS "LOSS_BATCH_VALID" ("EXPID" TEXT NOT NULL, "BATCH" INTEGER NOT NULL, "VALUE" REAL NOT NULL);',
            'CREATE TABLE IF NOT EXISTS "LOSS_EPOCH_TEST" ("EXPID" TEXT NOT NULL, "EPOCH" INTEGER NOT NULL, "VALUE" REAL NOT NULL);',
            'CREATE TABLE IF NOT EXISTS "LOSS_BATCH_TEST" ("EXPID" TEXT NOT NULL, "BATCH" INTEGER NOT NULL, "VALUE" REAL NOT NULL);',
            
            # metrics
            'CREATE TABLE IF NOT EXISTS "METRIC_RMSE_VALID" ("EXPID" TEXT NOT NULL, "VALUE" REAL NOT NULL);',
            'CREATE TABLE IF NOT EXISTS "METRIC_RMSE_TEST" ("EXPID" TEXT NOT NULL, "VALUE" REAL NOT NULL);',
            'CREATE TABLE IF NOT EXISTS "METRIC_R2_VALID" ("EXPID" TEXT NOT NULL, "VALUE" REAL NOT NULL);',
            'CREATE TABLE IF NOT EXISTS "METRIC_R2_TEST" ("EXPID" TEXT NOT NULL, "VALUE" REAL NOT NULL);',
            # TODO: other metrics? AP? IoU?

            # weights
            'CREATE TABLE IF NOT EXISTS "STATE_FINAL" ("EXPID" TEXT NOT NULL, "PATH" TEXT NOT NULL UNIQUE);',
            'CREATE TABLE IF NOT EXISTS "STATE_MIN_LOSS" ("EXPID" TEXT NOT NULL, "PATH" TEXT NOT NULL UNIQUE);',
            'CREATE TABLE IF NOT EXISTS "STATE_CHECKPOINT" ("EXPID" TEXT NOT NULL, "EPOCH" INTEGER NOT NULL, "PATH" TEXT NOT NULL UNIQUE);',

            # segmented images?
            # 'CREATE TABLE IF NOT EXISTS "SEGMENTED_IMAGES_EPOCH_TRAIN" ("EXPID" TEXT NOT NULL, "EPOCH" INTEGER NOT NULL, "SOURCE_IMAGE_PATH" TEXT NOT NULL, "SEGMENTED_IMAGE" BLOB NOT NULL);'

            # 'CREATE TABLE IF NOT EXISTS "STATUS" ("EXPID" TEXT NOT NULL, "STATUS" TEXT NOT NULL);'
            # 'CREATE TABLE IF NOT EXISTS "STATUS" ("EXPID" TEXT NOT NULL, "STATUS" TEXT NOT NULL);'
            # 'CREATE TABLE IF NOT EXISTS "STATUS" ("EXPID" TEXT NOT NULL, "STATUS" TEXT NOT NULL);'
            # 'CREATE TABLE IF NOT EXISTS "STATUS" ("EXPID" TEXT NOT NULL, "STATUS" TEXT NOT NULL);'
        ]
        for command in commands:
            self.cursor.execute(command)
        self.conn.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
