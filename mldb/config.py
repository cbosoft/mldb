import json
import os
import sys


class _Config:

    def __init__(self, db_path: str, **_):
        self.db_path = db_path

    @classmethod
    def load(cls):
        config_name = 'mldb_config.json'
        if sys.platform != 'Windows':
            config_name = '.' + config_name

        config_path = os.path.join(os.getenv('HOME'), config_name)

        try:
            with open(config_path) as f:
                config_data = json.load(f)
        except IOError as e:
            print('Error loading config:')
            print(e)
            print('Using default instead.')
            config_data = cls.defaults()

        return cls(**config_data)

    @classmethod
    def defaults(cls) -> dict:
        return dict(
            db_path=None
        )


CONFIG = _Config.load()
