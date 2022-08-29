import json

import torch
import numpy as np

from mldb.database.base import BaseDatabase


def test_sanitisation():
    assert BaseDatabase.sanitise_value(0.5) == 0.5
    assert BaseDatabase.sanitise_value(1) == 1
    assert BaseDatabase.sanitise_value((1, 2, 3)) == [1, 2, 3]
    assert sorted(BaseDatabase.sanitise_value({1, 2, 3})) == [1, 2, 3]

    assert BaseDatabase.sanitise_value(np.array([1, 2, 3], dtype=np.int32)) == [1, 2, 3]
    assert BaseDatabase.sanitise_value(np.array([[1.], [2], [3.]], dtype=np.float64)) == [[1.], [2.], [3.]]

    json.dumps(BaseDatabase.sanitise_value(np.array([1, 2, 3], dtype=np.int32)))
    json.dumps(BaseDatabase.sanitise_value(np.array([[1.], [2], [3.]], dtype=np.float64)))

    assert BaseDatabase.sanitise_value(torch.tensor([1, 2, 3], dtype=torch.int32)) == [1, 2, 3]
    assert BaseDatabase.sanitise_value(torch.tensor([[1.], [2], [3.]], dtype=torch.float64)) == [[1.], [2.], [3.]]

    json.dumps(BaseDatabase.sanitise_value(torch.tensor([1, 2, 3], dtype=torch.int32)))
    json.dumps(BaseDatabase.sanitise_value(torch.tensor([[1.], [2], [3.]], dtype=torch.float64)))
