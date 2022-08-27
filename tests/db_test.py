from datetime import datetime

from mldb.config import CONFIG
from mldb.database import Database


def test_db():

    CONFIG.host = 'tyke.db.elephantsql.com'
    CONFIG.database = CONFIG.user = 'fgwfjfjg'
    CONFIG.password = 'fd8TXM0-bmDAM46WVpD0LbtWw33lzP1g'
    CONFIG.port = 5432

    today = datetime.now().strftime('%Y%m%d%H%M%S')

    with Database() as db:
        db.set_exp_status(f'{today}_TEST_1', 'TRAINING')
        db.add_metric_value(f'{today}_TEST_1', 'RMSE', 1, 1.0)
        db.set_exp_status(f'{today}_TEST_1', 'COMPLETE')
        db.add_metric_value(f'{today}_TEST_1', 'RMSE', 2, 0.5)

        db.add_metric_value(f'{today}_TEST_2', 'RMSE', 1, 0.5)
        db.set_exp_status(f'{today}_TEST_2', 'TRAINING')
        db.add_metric_value(f'{today}_TEST_2', 'RMSE', 2, 0.25)
        db.set_exp_status(f'{today}_TEST_2', 'COMPLETE')

        db.add_metric_value(f'{today}_TEST_3', 'RMSE', 1, 0.25)
        db.set_exp_status(f'{today}_TEST_3', 'TRAINING')
        db.add_metric_value(f'{today}_TEST_3', 'RMSE', 2, 0.125)

        db.conn.commit()

        db.cursor.execute(
            'SELECT STATUS.EXPID FROM \
            STATUS INNER JOIN METRICS ON STATUS.EXPID=METRICS.EXPID \
            WHERE STATUS.STATUS=\'COMPLETE\' \
            AND METRICS.KIND=\'RMSE\' \
            AND METRICS.EXPID LIKE %s \
            ORDER BY METRICS.VALUE ASC LIMIT 1;', (f'{today}_TEST_%',))

        rows = db.cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == f'{today}_TEST_2'

        db.cursor.execute('DELETE FROM METRICS WHERE EXPID LIKE %s;', (f'{today}_TEST_%',))
        db.conn.commit()
