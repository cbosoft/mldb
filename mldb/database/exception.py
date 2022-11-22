class MLDBErrorBase(Exception):
    """Base error from which all MLDB-related errors derive"""


class NoDataError(MLDBErrorBase):
    """Error raised when no data is returned for a given query."""
