import os

from mldb.config import CONFIG
from mldb.database import Database


def test_db():
    CONFIG.db_path = 'test.db'
    CONFIG.database = 'Test'

    if os.path.isfile(CONFIG.db_path):
        os.remove(CONFIG.db_path)

    with Database() as db:
        db.set_exp_status('TEST_1', 'TRAINING')
        db.add_metric_value('TEST_1', 'RMSE', 1, 1.0)
        db.set_exp_status('TEST_1', 'COMPLETE')
        db.add_metric_value('TEST_1', 'RMSE', 2, 0.5)

        db.add_metric_value('TEST_2', 'RMSE', 1, 0.5)
        db.set_exp_status('TEST_2', 'TRAINING')
        db.add_metric_value('TEST_2', 'RMSE', 2, 0.25)
        db.set_exp_status('TEST_2', 'COMPLETE')

        db.add_metric_value('TEST_3', 'RMSE', 1, 0.25)
        db.set_exp_status('TEST_3', 'TRAINING')
        db.add_metric_value('TEST_3', 'RMSE', 2, 0.125)

        db.conn.commit()

        db.cursor.execute(
            'SELECT STATUS.EXPID FROM \
            STATUS INNER JOIN METRICS ON STATUS.EXPID=METRICS.EXPID \
            WHERE STATUS.STATUS=\'COMPLETE\' AND METRICS.KIND=\'RMSE\' \
            ORDER BY METRICS.VALUE ASC LIMIT 1;')

        rows = db.cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 'TEST_2'

        db.cursor.execute('drop table metrics;')
        db.conn.commit()
