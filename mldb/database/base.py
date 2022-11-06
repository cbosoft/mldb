import os
import json

import numpy as np


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

    def get_hyperparams(self, exp_id: str) -> dict:
        raise NotImplementedError

    def add_metric_value(self, exp_id: str, kind: str, epoch: int, value: float):
        raise NotImplementedError

    def set_config_file(self, exp_id, config_file_path: str):
        raise NotImplementedError

    def add_state_file(self, exp_id: str, epoch: int, path: str, error_on_collision=True):
        raise NotImplementedError

    def get_state_file(self, exp_id: str, epoch: int) -> str:
        raise NotImplementedError

    def get_experiment_details(self, exp_id) -> dict:
        raise NotImplementedError

    def get_latest_metrics(self, exp_id) -> dict:
        raise NotImplementedError

    def add_lr_value(self, exp_id: str, epoch: int, value: float):
        raise NotImplementedError

    def get_lr_values(self, exp_id: str):
        raise NotImplementedError

    @classmethod
    def sanitise_value(cls, v):
        if isinstance(v, (str, int, float)):
            return v
        elif hasattr(v, 'detach') and hasattr(v, 'cpu') and hasattr(v, 'numpy'):
            return cls.sanitise_value(v.detach().cpu().numpy())
        elif isinstance(v, (np.float16, np.float32, np.float64)):
            return float(v)
        elif isinstance(v, (np.int8, np.int16, np.int32, np.int64,
                            np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(v)
        elif hasattr(v, '__iter__'):
            return [cls.sanitise_value(vi) for vi in v]
        else:
            raise ValueError(f'Unexpected type encountered: {type(v)}.')

    def add_qualitative_result(self, exp_id: str, epoch: int, plot_id: str, output, target=None, **extra):
        data = dict(
            output=self.sanitise_value(output),
            **extra
        )
        if target is not None:
            data['target'] = self.sanitise_value(target)

        self.add_qualitative_result_json(
            exp_id,
            epoch,
            plot_id,
            json.dumps(data)
        )

    def add_qualitative_result_json(self, exp_id: str, epoch: int, plot_id: str, value: str):
        raise NotImplementedError

    def add_qualitative_metadata(self, exp_id: str, plot_id: str, kind: str, **meta_data):
        self.add_qualitative_metadata_json(exp_id, plot_id, json.dumps(dict(kind=kind, **meta_data)))

    def add_qualitative_metadata_json(self, exp_id: str, plot_id: str, value: str):
        raise NotImplementedError

    def get_qualitative_result(self, exp_id: str, plot_id: str):
        raise NotImplementedError

    def add_to_group(self, exp_id: str, group: str):
        raise NotImplementedError

    def remove_from_group(self, exp_id: str, group: str):
        raise NotImplementedError

    def get_group(self, group: str):
        raise NotImplementedError

    def get_groups_of_exp(self, expid: str):
        raise NotImplementedError
