from ..config import CONFIG

from .base import BaseDatabase
from .sqlite_backend import SQLiteDatabase
from .postgresql_backend import PostgreSQLDatabase
from .dummy import DummyDatabase

BACKEND_REGISTRY = dict(
    sqlite=SQLiteDatabase,
    postgresql=PostgreSQLDatabase,
    dummy=DummyDatabase
)


class Database(BaseDatabase):

    def __new__(cls):
        assert CONFIG.backend in BACKEND_REGISTRY, f'Backend "{CONFIG.backend}" not recognised.'
        return BACKEND_REGISTRY[CONFIG.backend]()
