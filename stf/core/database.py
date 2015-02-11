
import ZODB, ZODB.FileStorage
import ZODB.config
from ZODB import DB
from ZEO import ClientStorage
import persistent
import transaction
from datetime import datetime

from stf.common.out import *
from stf.core.experiment import __experiments__
from stf.core.dataset import __datasets__
from stf.core.connections import  __group_of_group_of_connections__


class Database:
    def __init__(self):
        self.db = ZODB.config.databaseFromURL('confs/zeo.conf')
        self.connection = self.db.open()
        self.root = self.connection.root()

        # Experiments
        try:
            __experiments__.experiments = self.root['experiments']
        except KeyError:
            self.root['experiments'] = __experiments__.experiments

        # Datasets
        try:
            __datasets__.datasets = self.root['datasets']
        except KeyError:
            self.root['datasets'] = __datasets__.datasets

        # Connections
        try:
            __group_of_group_of_connections__.group_of_connections = self.root['connections']
        except KeyError:
            self.root['connections'] = __group_of_group_of_connections__.group_of_connections

        # Models
        # Comparisons

    def list(self):
        print_info('Amount of experiments in the DB so far: {}'.format(len(self.root['experiments'])))
        print_info('Amount of datasets in the DB so far: {}'.format(len(self.root['datasets'])))
        print_info('Amount of connections in the DB so far: {}'.format(len(self.root['connections'])))

    def close(self):
        """ Close the db """
        transaction.commit()
        self.connection.close()
        self.db.close()

__database__ = Database()
