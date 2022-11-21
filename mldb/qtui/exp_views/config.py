import os.path

from PySide6.QtWidgets import QTextEdit, QTabWidget, QHBoxLayout
from PySide6.QtGui import QTextOption

from ...config import CONFIG
from ..db_iop import DBQuery
from .view_base import BaseExpView


class ExpConfigView(BaseExpView):

    QUERY = 'SELECT * FROM CONFIG WHERE EXPID=\'{0}\';'

    def __init__(self, *expids: str):
        if len(expids) > 3:
            expids = expids[:3]
            print('Too many experiments selected: only showing config of first three.')
        super().__init__(*expids)
        self.layout = QHBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.txt_boxes_by_id = {}
        for expid in self.expids:
            txt = self.get_config_text_box()
            self.tabs.addTab(txt, expid)
            self.txt_boxes_by_id[expid] = txt

        self.refresh()

    @staticmethod
    def get_config_text_box():
        txt = QTextEdit()
        txt.setReadOnly(True)
        # TODO: monaco on macos, consolas on windows
        txt.setFont('Monaco')
        txt.setWordWrapMode(QTextOption.NoWrap)
        txt.setText('<loading...>')
        return txt

    def refresh(self):
        for expid in self.expids:
            DBQuery(
                self.QUERY.format(expid),
                self.config_returned
            ).start()

    def config_returned(self, expid_and_path):
        expid, path = expid_and_path[0]

        full_path = os.path.join(CONFIG.root_dir, path)

        try:
            with open(full_path) as f:
                t = f.read()
            t = f'# {path}\n' + t
        except IOError as e:
            t = f'Could not read config for experiment {expid}.\n{e}'

        self.txt_boxes_by_id[expid].setText(t)
