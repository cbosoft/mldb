from mldb.config import CONFIG
from mldb.qtui import main

if __name__ == '__main__':

    # For debugging: you can change the server settings by hooking in to the CONFIG object before running main.
    # CONFIG.host = 'tyke.db.elephantsql.com'
    # CONFIG.database = CONFIG.user = 'fgwfjfjg'
    # CONFIG.password = 'fd8TXM0-bmDAM46WVpD0LbtWw33lzP1g'
    # CONFIG.port = 5432

    main()
