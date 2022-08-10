import json
import os


class SQLiteConfig:

    backend = 'sqlite'

    def __init__(self, db_path: str):
        self.db_path = db_path

    def as_dict(self):
        return dict(db_path=self.db_path)


class PostgreSQLConfig:

    backend = 'postgresql'

    def __init__(self, root_dir: str, host: str, password: str, user: str, database: str, port=5432):
        self.root_dir = root_dir
        self.host = host
        self.password = password
        self.user = user
        self.database = database
        self.port = port

    def as_dict(self):
        return dict(
            host=self.host,
            password=self.password,
            user=self.user,
            database=self.database,
            port=self.port
        )


class _Config:

    def __init__(self, *_, **__):
        """
        This constructor is never called.
        Meta class returns one of the above backend-specific
        config classes instead.
        """
        pass

    def __new__(cls, *, backend, **kwargs):
        if backend == 'sqlite':
            assert 'sqlite' in kwargs
            config = SQLiteConfig(**kwargs['sqlite'])
        elif backend == 'postgresql':
            assert 'postgresql' in kwargs
            config = PostgreSQLConfig(**kwargs['postgresql'])
        else:
            raise ValueError(f'Unknown backend {backend}')
        return config

    @classmethod
    def load(cls):
        config_name = '.mldb_config.json'

        config_path = os.path.join(os.getenv('HOME'), config_name)

        with open(config_path) as f:
            config_data = json.load(f)

        return cls(**config_data)


CONFIG = _Config.load()
