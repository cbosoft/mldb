import os


class BaseDatabase:

    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir if root_dir is not None else os.path.curdir

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def sanitise_path(self, path: str) -> str:
        return os.path.relpath(path, self.root_dir)

    def desanitise_path(self, sanitised_path: str) -> str:
        return os.path.join(self.root_dir, sanitised_path)

    def set_exp_status(self, exp_id: str, status: str):
        raise NotImplementedError

    def add_loss_value(self, exp_id: str, kind: str, epoch: int, value: float):
        raise NotImplementedError

    def add_hyperparam(self, exp_id: str, name: str, value: str):
        raise NotImplementedError

    def add_metric_value(self, exp_id: str, kind: str, epoch: int, value: float):
        raise NotImplementedError

    def set_config_file(self, exp_id, config_file_path: str):
        raise NotImplementedError

    def add_state_file(self, exp_id: str, epoch: int, path: str, error_on_collision=True):
        raise NotImplementedError

    def get_state_file(self, exp_id: str, epoch: int) -> str:
        raise NotImplementedError
