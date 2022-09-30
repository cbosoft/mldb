from PySide6 import QtWidgets

from .status_display import StatusDisplay
from .exp_list import ExperimentListWidget
from .model_list import ModelListWidget


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        self.status_display = StatusDisplay(self)
        layout = central_widget.layout = QtWidgets.QVBoxLayout(central_widget)
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)

        # self.tabs.addTab(QtWidgets.QWidget(), 'Welcome')

        self.exp_list = ExperimentListWidget()
        self.exp_list.status_signal.connect(self.status_display.show_message)
        self.exp_list.progress_signal.connect(self.status_display.set_progress)
        self.tabs.addTab(self.exp_list, 'Experiments')

        self.model_list = ModelListWidget()
        self.model_list.status_signal.connect(self.status_display.show_message)
        self.model_list.progress_signal.connect(self.status_display.set_progress)
        self.tabs.addTab(self.model_list, 'Models')

        self.resize(720, 720)

    def setup_menu(self):
        self.setWindowTitle(f'Foo v0.0.0')
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')
        export_action = file_menu.addAction('Export')
        file_menu.addSeparator()
        exit_action = file_menu.addAction('Exit')

        measurements_menu = menu_bar.addMenu('Measurements')
        import_images_action = measurements_menu.addAction('Images')
        import_fbrm_action = measurements_menu.addAction('FBRM CLD')
        # other cld sources e.g. blaze metrics ?
        # other measurements...
        # TODO

        # measurements_menu = menu_bar.addMenu('Contstraints')
        # TODO

        analyses_menu = menu_bar.addMenu('Analyses')
        analysis_settings_action = analyses_menu.addAction('Analysis Settings')

        help_menu = menu_bar.addMenu('Help')
        show_help_action = help_menu.addAction('Show Help')
        help_menu.addSeparator()
        about_action = help_menu.addAction('About')

        return export_action, exit_action, import_images_action, import_fbrm_action, analysis_settings_action, show_help_action, about_action
