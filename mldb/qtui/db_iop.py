from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from mldb import Database


class DBQuery(QObject):

    results_returned = Signal(list)

    def __init__(self, query: str, slot=None):
        super().__init__()
        self.query = _DBQueryWorker(query, lambda rows: self.results_returned.emit(rows))
        if slot:
            self.results_returned.connect(slot)

    def start(self):
        self.query.start()


class _DBQueryWorker(QRunnable):

    def __init__(self, query: str, cb):
        super().__init__()
        self.query = query
        self.cb = cb

    def run(self):
        with Database() as db:
            db.cursor.execute(self.query)
            results = db.cursor.fetchall()
        self.cb(results)

    def start(self):
        QThreadPool.globalInstance().start(self)


class DBExpDetails(QObject):

    results_returned = Signal(dict)

    def __init__(self, expid: str, slot=None):
        super().__init__()
        self.query = _DBExpDetailsWorker(expid, lambda rv: self.results_returned.emit(rv))
        if slot:
            self.results_returned.connect(slot)

    def start(self):
        self.query.start()


class _DBExpDetailsWorker(QRunnable):

    def __init__(self, expid: str, cb):
        super().__init__()
        self.expid = expid
        self.cb = cb

    def run(self):
        with Database() as db:
            rv = db.get_experiment_details(self.expid)
        self.cb(rv)

    def start(self):
        QThreadPool.globalInstance().start(self)


class DBExpMetrics(QObject):

    results_returned = Signal(dict)

    def __init__(self, expid: str, slot=None):
        super().__init__()
        self.query = _DBExpMetricsWorker(expid, lambda metrics: self.results_returned.emit(metrics))
        if slot:
            self.results_returned.connect(slot)

    def start(self):
        self.query.start()


class _DBExpMetricsWorker(QRunnable):

    def __init__(self, expid: str, cb):
        super().__init__()
        self.expid = expid
        self.cb = cb

    def run(self):
        with Database() as db:
            metrics = db.get_latest_metrics(self.expid)
        self.cb(metrics)

    def start(self):
        QThreadPool.globalInstance().start(self)


class DBExpQualResults(QObject):

    results_returned = Signal(dict)

    def __init__(self, expid: str, slot=None, plots=None):
        super().__init__()
        self.query = _DBExpQualResultsWorker(expid, lambda qualres: self.results_returned.emit(qualres), plots)
        if slot:
            self.results_returned.connect(slot)

    def start(self):
        self.query.start()


class _DBExpQualResultsWorker(QRunnable):

    def __init__(self, expid: str, cb, plots=None):
        super().__init__()
        self.expid = expid
        self.cb = cb
        self.plotids = plots

    def run(self):
        with Database() as db:
            qualres = []
            if not self.plotids:
                db.cursor.execute('SELECT PLOTID FROM QUALITATIVERESULTSMETA WHERE EXPID=%s', (self.expid,))
                self.plotids = db.cursor.fetchall()
                print('plot ids', self.plotids)

            for plotid in self.plotids:
                plotid = plotid[0]
                qualres.append((plotid, db.get_qualitative_result(self.expid, plotid)))
        self.cb(qualres)

    def start(self):
        QThreadPool.globalInstance().start(self)


class DBExpHyperParams(QObject):

    results_returned = Signal(dict)

    def __init__(self, expid: str, slot=None):
        super().__init__()
        self.query = _DBExpHyperParamsWorker(expid, lambda hparams: self.results_returned.emit(hparams))
        if slot:
            self.results_returned.connect(slot)

    def start(self):
        self.query.start()


class _DBExpHyperParamsWorker(QRunnable):

    def __init__(self, expid: str, cb):
        super().__init__()
        self.expid = expid
        self.cb = cb

    def run(self):
        with Database() as db:
            hparams = db.get_hyperparams(self.expid)
        self.cb(hparams)

    def start(self):
        QThreadPool.globalInstance().start(self)


class DBMethod(QObject):

    results_returned = Signal(object)

    def __init__(self, method, *args: tuple, slot=None):
        super().__init__()
        self.query = _DBMethodWorker(method, *args, cb=lambda rows: self.results_returned.emit(rows))
        if slot:
            self.results_returned.connect(slot)

    def start(self):
        self.query.run()


class _DBMethodWorker(QRunnable):

    def __init__(self, method, *argss, cb):
        super().__init__()
        self.method = method
        self.argss = argss
        self.cb = cb

    def run(self):
        with Database() as db:
            for args in self.argss:
                self.cb(self.method(db, *args))
