
import ZODB, ZODB.FileStorage
import persistent
import transaction
from datetime import datetime

from stf.common.out import *
from stf.core.experiment import __experiments__



class Database:
    def __init__(self):
        #print_info('Setting up the DB')
        self.storage = ZODB.FileStorage.FileStorage('/tmp/stf.zodb')
        self.db = ZODB.DB(self.storage)

        # During testing just create it on memory
        #db = ZODB.DB(None)

        self.connection = self.db.open()
        self.root = self.connection.root()

        # Experiments
        try:
            e = self.root['experiments']
            #print_info('Amount of experiments in the DB: {}'.format(len(e)))
            __experiments__.experiments = e
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
