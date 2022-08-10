from ..config import CONFIG

from .base import BaseDatabase
from .sqlite_backend import SQLiteDatabase
from .postgresql_backend import PostgreSQLDatabase

BACKEND_REGISTRY = dict(
    sqlite=SQLiteDatabase,
    postgresql=PostgreSQLDatabase
)


class Database(BaseDatabase):

    def __new__(cls):
        assert CONFIG.backend in BACKEND_REGISTRY, f'Backend "{CONFIG.backend}" not recognised.'
        return BACKEND_REGISTRY[CONFIG.backend]()

    """
    This is a meta class which is not actually used. The functions below are implemented in the sub classes
    (SQLiteDatabase, PostGreSQLDatabase, etc). They are written here to appease the almightly linter.
    """

    def __repr__(self):
        ...

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

    def add_metric_value(self, exp_id: str, kind: str, epoch: int, value: float):
        ...

    def set_config_file(self, exp_id, config_file_path: str):
        ...

    def add_state_file(self, exp_id: str, epoch: int, path: str, error_on_collision=True):
        ...

    def get_state_file(self, exp_id: str, epoch: int) -> str:
        ...
