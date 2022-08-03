# MLDB

A machine learning model database facilitator: SQLite database + python convenience.

mldb helps maintain a databse of model stats while they are training, as well as a record of trained model weights (during and) after training has completed.

This is intended to help keep track of models, especially in cases where many experiments are being run (e.g. as part of hyperparameter optimisation).

"Small" data, like loss values and metrics, are stored directly in the databse, while large blobs of data (segmented images, plots, model state) are left on the filesystem and "pointed to" by the apropriate database entry. (That's a long, needlessly complicated way of saying only a file path is stored.)

# Getting started

The database configuration is specified in JSON in your home directory. If this file is not specified, you may specify config within a python script by amending the global variable `CONFIG`, but it is preferred to write out the config:

`$HOME/.mldb_config.json` or, if you're on Windows, `$HOME\mldb_config.json`
```json
{
  "db_path": "/path/to/database.db"
}
```

To use the database, you can use the context manager and execute sql directly:
```python
from mldb import Database

with Database() as db:
    db.cursor.execute('SELECT EXP_ID FROM STATUS WHERE STATUS.STATUS="COMPLETE";')
    print(db.cursor.fetchall())
```