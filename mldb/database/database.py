import os
import json
from typing import List

import numpy as np
from psycopg2 import connect
import psycopg2.sql as sql

from ..config import CONFIG
from .schema import SCHEMA, TABLES
from .exception import NoDataError


class Database:

    COMMAND_SET_STATUS = "INSERT INTO STATUS (EXPID, STATUS) VALUES (%s, %s) ON CONFLICT (EXPID) DO UPDATE SET STATUS=excluded.STATUS;"
    COMMAND_GET_STATUS = "SELECT * FROM STATUS WHERE EXPID=%s;"
    COMMAND_ADD_LOSS = (
        "INSERT INTO LOSS (EXPID, KIND, EPOCH, VALUE) VALUES (%s, %s, %s, %s)"
    )
    COMMAND_GET_LOSSES = "SELECT * FROM LOSS WHERE EXPID=%s;"
    COMMAND_ADD_HYPERPARAM = (
        "INSERT INTO HYPERPARAMS (EXPID, NAME, VALUE) VALUES (%s, %s, %s)"
    )
    COMMAND_GET_HYPERPARAMS = "SELECT * FROM HYPERPARAMS WHERE EXPID=%s;"
    COMMAND_ADD_METRICS = (
        "INSERT INTO METRICS (EXPID, KIND, EPOCH, VALUE) VALUES (%s, %s, %s, %s);"
    )
    COMMAND_GET_LATEST_METRICS = "SELECT * FROM METRICS WHERE (EXPID, EPOCH) IN (SELECT EXPID, max(EPOCH) FROM METRICS WHERE EXPID=%s GROUP BY EXPID);"
    COMMAND_SET_CONFIG = "INSERT INTO CONFIG (EXPID, CONFIG) VALUES (%s, %s);"
    COMMAND_ADD_STATE = "INSERT INTO STATE (EXPID, EPOCH, PATH) VALUES (%s, %s, %s);"
    COMMAND_GET_STATE = "SELECT PATH FROM STATE WHERE EXPID=? AND EPOCH=%s;"
    COMMAND_GET_EXPERIMENT_DETAILS = "SELECT * FROM STATUS INNER JOIN LOSS ON status.expid=loss.expid WHERE status.expid=%s;"
    COMMAND_ADD_LR = (
        "INSERT INTO LEARNINGRATE (EXPID, EPOCH, VALUE) VALUES (%s, %s, %s)"
    )
    COMMAND_GET_LRS = (
        "SELECT (EPOCH, VALUE) FROM LEARNINGRATE WHERE EXPID=%s ORDER BY EPOCH;"
    )
    COMMAND_ADD_QUALRESMETA = (
        "INSERT INTO QUALITATIVERESULTSMETA (EXPID, PLOTID, VALUE) VALUES (%s, %s, %s)"
    )
    COMMAND_ADD_QUALRES = "INSERT INTO QUALITATIVERESULTS (EXPID, EPOCH, PLOTID, VALUE) VALUES (%s, %s, %s, %s)"
    COMMAND_GET_QUALRES = (
        "SELECT * FROM QUALITATIVERESULTS WHERE EXPID=%s AND PLOTID=%s;"
    )
    COMMAND_GET_QUALRESMETA = (
        "SELECT * FROM QUALITATIVERESULTSMETA WHERE EXPID=%s AND PLOTID=%s;"
    )
    COMMAND_ADD_TO_GROUP = "INSERT INTO EXPGROUPS (EXPID, GROUPNAME) VALUES (%s, %s);"
    COMMAND_REMOVE_FROM_GROUP = "DELETE FROM EXPGROUPS WHERE EXPID=%s AND GROUPNAME=%s;"
    COMMAND_GET_GROUP = "SELECT EXPID FROM EXPGROUPS WHERE GROUPNAME=%s;"
    COMMAND_GET_GROUPS_OF_EXP = "SELECT GROUPNAME FROM EXPGROUPS WHERE EXPID=%s;"
    COMMAND_DELETE_EXPERIMENT = "DELETE FROM {} WHERE EXPID=%s;"

    TABLES = TABLES

    def __init__(self):
        self.root_dir = CONFIG.root_dir
        self.host = CONFIG.host
        self.user = CONFIG.user
        self.port = CONFIG.port
        self.database = CONFIG.database
        self.conn = None
        self.cursor = None

        self.connect()
        self.ensure_schema()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        return f"PostgreSQL://{self.user}@{self.host}:{self.port}/{self.database}"

    def sanitise_path(self, path: str) -> str:
        return os.path.relpath(path, self.root_dir)

    def desanitise_path(self, sanitised_path: str) -> str:
        return os.path.join(self.root_dir, sanitised_path)

    @classmethod
    def sanitise_value(cls, v):
        if isinstance(v, (str, int, float)):
            return v
        elif hasattr(v, "detach") and hasattr(v, "cpu") and hasattr(v, "numpy"):
            return cls.sanitise_value(v.detach().cpu().numpy())
        elif isinstance(v, (np.float16, np.float32, np.float64)):
            return float(v)
        elif isinstance(
            v,
            (
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):
            return int(v)
        elif hasattr(v, "__iter__"):
            return [cls.sanitise_value(vi) for vi in v]
        else:
            raise ValueError(f"Unexpected type encountered: {type(v)}.")

    def add_qualitative_result(
        self, exp_id: str, epoch: int, plot_id: str, output, target=None, **extra
    ):
        data = dict(output=self.sanitise_value(output), **extra)
        if target is not None:
            data["target"] = self.sanitise_value(target)

        self.add_qualitative_result_json(exp_id, epoch, plot_id, json.dumps(data))

    def connect(self):
        self.conn = connect(**CONFIG.as_dict())
        self.cursor = self.conn.cursor()

    def run_query(self, *commands):
        for command in commands:
            self.cursor.execute(command)

    def run_query_and_commit(self, *commands):
        self.run_query(*commands)
        self.conn.commit()

    def run_query_and_fetch(self, *commands):
        self.run_query(*commands)
        return self.cursor.fetchall()

    def ensure_schema(self):
        self.run_query_and_commit(*SCHEMA)

    def close(self):
        self.conn.close()

    def set_exp_status(self, exp_id: str, status: str):
        self.cursor.execute(self.COMMAND_SET_STATUS, (exp_id, status))
        self.conn.commit()

    def add_loss_value(self, exp_id: str, kind: str, epoch: int, value: float):
        self.cursor.execute(self.COMMAND_ADD_LOSS, (exp_id, kind, epoch, value))
        self.conn.commit()

    def add_hyperparam(self, exp_id: str, name: str, value: str):
        self.cursor.execute(self.COMMAND_ADD_HYPERPARAM, (exp_id, name, value))
        self.conn.commit()

    def get_hyperparams(self, exp_id: str) -> dict:
        self.cursor.execute(self.COMMAND_GET_HYPERPARAMS, (exp_id,))
        results = self.cursor.fetchall()

        rv = dict()
        for (_, k, v) in results:
            rv[k] = v
        return rv

    def add_metric_value(self, exp_id: str, kind: str, epoch: int, value: float):
        self.cursor.execute(self.COMMAND_ADD_METRICS, (exp_id, kind, epoch, value))
        self.conn.commit()

    def set_config_file(self, exp_id, config_file_path: str):
        config_file_path = self.sanitise_path(config_file_path)
        self.cursor.execute(self.COMMAND_SET_CONFIG, (exp_id, config_file_path))
        self.conn.commit()

    def add_state_file(
        self, exp_id: str, epoch: int, path: str, error_on_collision=True
    ):
        path = self.sanitise_path(path)
        try:
            self.cursor.execute(self.COMMAND_ADD_STATE, (exp_id, epoch, path))
            self.conn.commit()
        except Exception as e:
            if error_on_collision:
                raise e
            self.conn.rollback()

    def get_state_file(self, expid: str, epoch: int) -> str:
        self.cursor.execute(self.COMMAND_GET_STATE, (expid, epoch))
        results = self.cursor.fetchall()
        if not results:
            raise NoDataError(
                f'No state file found for experiment "{expid}" at epoch {epoch}'
            )

        state_file = results[0][0]
        return self.desanitise_path(state_file)

    def get_status(self, expid: str) -> str:
        self.cursor.execute(self.COMMAND_GET_STATUS, (expid,))
        results = self.cursor.fetchall()

        if not results:
            raise NoDataError(f'No status information found for experiment "{expid}"')

        status = results[0][1]
        return status

    def get_losses(self, expid: str) -> dict:
        self.cursor.execute(self.COMMAND_GET_LOSSES, (expid,))
        results = self.cursor.fetchall()

        if not results:
            raise NoDataError(f'No losses found for experiment "{expid}"')
        res_by_cols = list(zip(*results))

        epochs = res_by_cols[1]
        loss_kinds = res_by_cols[2]
        losses = res_by_cols[3]
        uniq_kinds = set(loss_kinds)

        return {
            k: dict(
                loss=[l for l, lk in zip(losses, loss_kinds) if lk == k],
                epoch=[e for e, lk in zip(epochs, loss_kinds) if lk == k],
            )
            for k in uniq_kinds
        }

    def get_lrs(self, expid: str) -> dict:
        lr_es, lrs = [], []
        for lr in self.get_lr_values(expid):
            e, lr = lr[0][1:-1].split(",")
            lr_es.append(int(e))
            lrs.append(float(lr))
        return dict(epochs=lr_es, lrs=lrs)

    def get_experiment_details(self, expid: str) -> dict:
        return dict(
            expid=expid,
            status=self.get_status(expid),
            losses=self.get_losses(expid),
            lrs=self.get_lrs(expid),
        )

    def get_latest_metrics(self, exp_id) -> dict:
        self.cursor.execute(self.COMMAND_GET_LATEST_METRICS, (exp_id,))
        results = self.cursor.fetchall()

        if not results:
            return dict()

        return dict(
            expid=exp_id,
            epoch=results[0][1],
            data={kind: value for _, __, kind, value in results},
        )

    def add_lr_value(self, exp_id: str, epoch: int, value: float):
        self.cursor.execute(self.COMMAND_ADD_LR, (exp_id, epoch, value))
        self.conn.commit()

    def get_lr_values(self, exp_id: str):
        self.cursor.execute(self.COMMAND_GET_LRS, (exp_id,))
        return self.cursor.fetchall()

    def add_qualitative_metadata_json(self, exp_id: str, plot_id: str, value: str):
        self.cursor.execute(self.COMMAND_ADD_QUALRESMETA, (exp_id, plot_id, value))
        self.conn.commit()

    def add_qualitative_result_json(
        self, exp_id: str, epoch: int, plot_id: str, value: str
    ):
        self.cursor.execute(self.COMMAND_ADD_QUALRES, (exp_id, epoch, plot_id, value))
        self.conn.commit()

    def add_qualitative_metadata(
        self, exp_id: str, plot_id: str, kind: str, **meta_data
    ):
        self.add_qualitative_metadata_json(
            exp_id, plot_id, json.dumps(dict(kind=kind, **meta_data))
        )

    def get_qualitative_result(self, exp_id: str, plot_id: str):
        self.cursor.execute(self.COMMAND_GET_QUALRESMETA, (exp_id, plot_id))
        meta_enc = self.cursor.fetchall()

        qualres = json.loads(meta_enc[0][-1])

        self.cursor.execute(self.COMMAND_GET_QUALRES, (exp_id, plot_id))
        data = self.cursor.fetchall()

        qualres["data"] = []
        for row in data:
            # columns = ['expid', 'epoch', 'plotid', 'value']
            qualres["data"].append(dict(epoch=int(row[1]), **json.loads(row[-1])))

        return qualres

    def add_to_group(self, exp_id: str, group: str):
        self.cursor.execute(self.COMMAND_ADD_TO_GROUP, (exp_id, group))
        self.conn.commit()

    def add_many_to_group(self, expids_and_groups):
        for expid, group in expids_and_groups:
            self.cursor.execute(self.COMMAND_ADD_TO_GROUP, (expid, group))
        self.conn.commit()

    def remove_from_group(self, exp_id: str, group: str):
        self.cursor.execute(self.COMMAND_REMOVE_FROM_GROUP, (exp_id, group))
        self.conn.commit()

    def remove_many_from_group(self, expids_and_groups):
        for expid, group in expids_and_groups:
            self.cursor.execute(self.COMMAND_REMOVE_FROM_GROUP, (expid, group))
        self.conn.commit()

    def get_group(self, group: str):
        self.cursor.execute(self.COMMAND_GET_GROUP, (group,))
        expids = [r[0] for r in self.cursor.fetchall()]
        return expids

    def get_groups_of_exp(self, expid: str):
        self.cursor.execute(self.COMMAND_GET_GROUPS_OF_EXP, (expid,))
        groups = [r[0] for r in self.cursor.fetchall()]
        return groups

    def get_groups_of_many_exps(self, expids: List[str]):
        condition = sql.SQL("")
        for i, expid in enumerate(expids):
            expid = sql.Literal(expid)
            if i:
                condition += sql.SQL(" OR ")
            condition += sql.SQL(" EXPID={expid} ").format(expid=expid)
        q = sql.SQL(
            "SELECT DISTINCT GROUPNAME FROM EXPGROUPS WHERE {condition};"
        ).format(condition=condition)
        self.cursor.execute(q)
        groups = [r[0] for r in self.cursor.fetchall()]
        return groups

    def delete_experiment(self, exp_id: str):
        for table in self.TABLES:
            self.cursor.execute(self.COMMAND_DELETE_EXPERIMENT.format(table), (exp_id,))
        self.conn.commit()
        return exp_id
