
import ZODB, ZODB.FileStorage
import persistent
import transaction
from datetime import datetime

from stf.common.out import *
from stf.core.experiment import __experiments__


class Database:
    def __init__(self):
        self.storage = ZODB.FileStorage.FileStorage('temp-db/stf.zodb')
        self.db = ZODB.DB(self.storage)
        self.connection = self.db.open()
        self.root = self.connection.root()

        # Experiments
        try:
            __experiments__.experiments = self.root['experiments']
        except KeyError:
            self.root['experiments'] = __experiments__.experiments

        # Datasets
        # Connections
        # Models
        # Comparisons

    def list(self):
        print_info('Amount of experiments in the DB so far: {}'.format(len(self.root['experiments'])))

    def close(self):
        """ Close the db """
        transaction.commit()
        self.connection.close()
        self.db.close()
        self.storage.close()

__database__ = Database()
