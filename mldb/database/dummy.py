from .base import BaseDatabase


class DummyDatabase(BaseDatabase):

    def __init__(self, **_):
        super().__init__()

    def __repr__(self) -> str:
        return 'DummyDB'

    def connect(self):
        ...

    def close(self):
        ...

    def set_exp_status(self, exp_id: str, status: str):
        ...

    def add_loss_value(self, exp_id: str, kind: str, epoch: int, value: float):
        ...

    def add_hyperparam(self, exp_id: str, name: str, value: str):
        ...

    def get_hyperparams(self, exp_id: str) -> dict:
        ...

    def add_metric_value(self, exp_id: str, kind: str, epoch: int, value: float):
        ...

    def set_config_file(self, exp_id, config_file_path: str):
        ...

    def add_state_file(self, exp_id: str, epoch: int, path: str, error_on_collision=True):
        ...

    def get_state_file(self, exp_id: str, epoch: int) -> str:
        ...

    def get_experiment_details(self, exp_id) -> dict:
        ...

    def get_latest_metrics(self, exp_id) -> dict:
        ...

    def add_lr_value(self, exp_id: str, epoch: int, value: float):
        ...

    def get_lr_values(self, exp_id: str):
        ...

    def add_qualitative_result(self, exp_id: str, epoch: int, plot_id: str, output, target=None, **extra):
        ...

    def add_qualitative_result_json(self, exp_id: str, epoch: int, plot_id: str, value: str):
        raise NotImplementedError

    def add_qualitative_metadata(self, exp_id: str, plot_id: str, kind: str, **meta_data):
        ...

    def add_qualitative_metadata_json(self, exp_id: str, plot_id: str, value: str):
        ...

    def get_qualitative_result(self, exp_id: str, plot_id: str):
        ...
