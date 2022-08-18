from typing import Optional
import os
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer

from ..database import Database

SERVER_SOURCE_DIR = os.path.join(os.path.dirname(__file__), 'site')


class MLDB_Handler(SimpleHTTPRequestHandler):

    db: Database = None

    def run_query(self, query: dict) -> dict:
        if query['show'] == 'details':
            return self.get_experiment_details(query['expid'])
        elif query['kind'] == 'all':
            return self.get_status_table()
        elif query['kind'] == 'completed':
            return self.get_completed_experiments_table()
        elif query['kind'] == 'running':
            return self.get_running_experiments_table()
        else:
            return dict(error=True, why=f'unhandled query, unknown kind: {query}')

    def do_GET(self) -> None:

        if self.path in {'/', '/index.html'}:
            path = self.path + '?'
        else:
            path = self.path

        parts = path.split('?')

        if len(parts) > 1:
            path, query = parts

            if query:
                query = dict([tuple(p.split('=')) for p in query.split('&')])
                if query['show'] == 'about':
                    js = 'display_about();'
                elif query['show'] in {'status', 'details'}:

                    obj = self.run_query(query)

                    if obj is not None:
                        obj_str = json.dumps(obj).replace('"', '\\"')
                        js = f'var RESULT_STR = "{obj_str}"; var RESULT_OBJ = JSON.parse(RESULT_STR); display_result(RESULT_OBJ);'
                    else:
                        js = ''
                else:
                    print(f'unhandled query: {query}')
                    js = ''
            else:
                js = ''

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            with open('index.html', 'r') as f:
                index_html = f.read()

            index_html = (index_html
                          .replace('//SCRIPT GOES HERE//', js)
                          .replace('<!--CONNINFO-->', repr(self.db)))

            self.wfile.write(index_html.encode())
        else:
            super().do_GET()

    def get_post_content(self) -> str:
        content_len = int(self.headers.get('Content-Length'))
        return self.rfile.read(content_len).decode()

    def do_POST(self):
        query = json.loads(self.get_post_content())
        result = self.run_query(query)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())


    def get_running_experiments_table(self) -> dict:
        _ = self.db
        self.db.cursor.execute('SELECT * FROM status WHERE status.status=\'TRAINING\';')
        rows = self.db.cursor.fetchall()
        if rows:
            experiments, statuses = zip(*rows)
        else:
            experiments, statuses = [], []

        result = dict(
            title='Running Experiments',
            kind='status_table',
            headings=['EXPID', 'STATUS'],
            experiments=experiments,
            statuses=statuses
        )
        return result

    def get_completed_experiments_table(self) -> dict:
        self.db.cursor.execute('SELECT * FROM status WHERE status.status=\'COMPLETE\';')
        rows = self.db.cursor.fetchall()
        if rows:
            experiments, statuses = zip(*rows)
        else:
            experiments, statuses = [], []

        result = dict(
            title='Completed Experiments',
            kind='status_table',
            headings=['EXPID', 'STATUS'],
            experiments=experiments,
            statuses=statuses
        )
        return result

    def get_status_table(self) -> dict:
        self.db.cursor.execute('SELECT * FROM status;')
        rows = self.db.cursor.fetchall()
        if rows:
            experiments, statuses = zip(*rows)
        else:
            experiments, statuses = [], []

        result = dict(
            title='Experiment Status',
            kind='status_table',
            headings=['EXPID', 'STATUS'],
            experiments=experiments,
            statuses=statuses
        )
        return result

    def get_experiment_details(self, expid) -> dict:
        details = self.db.get_experiment_details(expid)
        if 'error' in details:
            return details

        params = self.db.get_hyperparams(expid)
        if 'error' in params:
            return params

        # TODO: config (dataset, most importantly)
        # config = self.db.get_config(expid)
        # if 'error' in config:
        #     return config

        raw_metrics = self.db.get_latest_metrics(expid)
        if 'error' in raw_metrics:
            return raw_metrics

        metrics = dict(epoch=raw_metrics['epoch'], expid=raw_metrics['expid'], low_data=dict(), high_data=dict())
        for k, v in raw_metrics['data'].items():
            if 'error' in k.lower() or k in {'RMSE', 'MSE', 'SSE'}:
                metrics['low_data'][k] = v
            else:
                metrics['high_data'][k] = v

        result = dict(
            title=f'Experiment Details ({expid})',
            kind='details',
            details=details,
            params=params,
            # config=config,
            metrics=metrics
        )

        # If is still training, refresh data every 30 seconds
        if 'status' in details:
            if details['status'] == 'TRAINING':
                result['refresh'] = dict(
                    query=dict(
                        show='details',
                        expid=expid
                    ),
                    period=30_000
                )

        return result


def run_server(hostname: str, port: int):
    os.chdir(SERVER_SOURCE_DIR)
    with Database() as MLDB_Handler.db:
        print(f'Connected to database "{MLDB_Handler.db}"')
        server = HTTPServer((hostname, port), MLDB_Handler)
        print(f'Server started: http://{hostname}:{port}')

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
            print('Server stopped.')
