import json
import os


class PostgreSQLConfig:

    backend = "postgresql"

    def __init__(
        self,
        root_dir: str,
        host: str,
        password: str,
        user: str,
        database: str,
        port=5432,
    ):
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
            port=self.port,
        )

    @classmethod
    def load(cls):
        config_name = ".mldb_config.json"

        home = os.getenv("HOME")
        if home is None:
            home = os.getenv("USERPROFILE")
        assert home is not None, "Could not find home!"

        config_path = os.path.join(home, config_name)

        with open(config_path) as f:
            config_data = json.load(f)

        if "backend" in config_data:
            assert (
                config_data["backend"] == "postgresql"
            ), "Only postgresql backed is supported. SQLite support has been removed."
            config_data = config_data["postgresql"]

        return cls(**config_data)


CONFIG = PostgreSQLConfig.load()
