import os

from mldb.config import CONFIG
from mldb.database import Database


def test_db():
    CONFIG.db_path = 'test.db'

    os.remove(CONFIG.db_path)

    with Database() as db:
        db.cursor.execute('INSERT INTO STATUS (EXPID, STATUS) VALUES (?, ?)', ('TEST_1', 'COMPLETE'))
        db.cursor.execute('INSERT INTO STATUS (EXPID, STATUS) VALUES (?, ?)', ('TEST_2', 'COMPLETE'))
        db.cursor.execute('INSERT INTO STATUS (EXPID, STATUS) VALUES (?, ?)', ('TEST_3', 'TRAINING'))

        db.cursor.execute('INSERT INTO METRIC_RMSE_VALID (EXPID, VALUE) VALUES (?, ?)', ('TEST_1', 0.5))
        db.cursor.execute('INSERT INTO METRIC_RMSE_VALID (EXPID, VALUE) VALUES (?, ?)', ('TEST_2', 0.25))
        db.cursor.execute('INSERT INTO METRIC_RMSE_VALID (EXPID, VALUE) VALUES (?, ?)', ('TEST_3', 0.1))

        db.conn.commit()

        db.cursor.execute('SELECT STATUS.EXPID FROM STATUS INNER JOIN METRIC_RMSE_VALID ON STATUS.EXPID=METRIC_RMSE_VALID.EXPID WHERE STATUS.STATUS="COMPLETE" ORDER BY METRIC_RMSE_VALID.VALUE ASC LIMIT 1;')
        rows = db.cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 'TEST_2'
