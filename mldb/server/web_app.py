import os
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer

from ..database import Database

SERVER_SOURCE_DIR = os.path.join(os.path.dirname(__file__), 'site')


class MLDB_Handler(SimpleHTTPRequestHandler):

    db: Database = None

    def do_GET(self) -> None:
        super().do_GET()

    def get_post_content(self) -> str:
        content_len = int(self.headers.get('Content-Length'))
        return self.rfile.read(content_len).decode()

    def do_POST(self) -> None:

        # parse path, run query, return results

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        query = json.loads(self.get_post_content())['query']

        if query == 'all_status':
            result = self.get_status_table()
        elif query == 'completed':
            result = self.get_completed_experiments_table()
        elif query == 'running':
            result = self.get_running_experiments_table()
        else:
            raise ValueError(f'Unknown query: {query}')

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
        _ = self.db
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
        _ = self.db
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
