import ZODB.config
import persistent
import transaction
import time
from datetime import datetime

from stf.core.configuration import __configuration__
from stf.common.out import *
from stf.core.experiment import __experiments__
from stf.core.dataset import __datasets__
from stf.core.connections import  __group_of_group_of_connections__
from stf.core.models import __groupofgroupofmodels__
from stf.core.notes import __notes__

class Database:
    def __init__(self):
        """ Initialize """
        pass

    def start(self):
        """ From some reason we should initialize the db from a method, we can not do it in the constructor """
        dbconffile = __configuration__.get_zodbconf_file()
        self.db = ZODB.config.databaseFromURL(dbconffile)
        
        # The server and port should be read from a future configuration
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
        try:
            __groupofgroupofmodels__.group_of_models = self.root['models']
        except KeyError:
            self.root['models'] = __groupofgroupofmodels__.group_of_models

        # Notes
        try:
            __notes__.notes = self.root['notes']
        except KeyError:
            self.root['notes'] = __notes__.notes

        # Comparisons

    def list(self):
        print_info('Amount of experiments in the DB so far: {}'.format(len(self.root['experiments'])))
        print_info('Amount of datasets in the DB so far: {}'.format(len(self.root['datasets'])))
        print_info('Amount of groups of connections in the DB so far: {}'.format(len(self.root['connections'])))
        print_info('Amount of groups of models in the DB so far: {}'.format(len(self.root['models'])))
        print_info('Amount of notes in the DB so far: {}'.format(len(self.root['notes'])))

    def close(self):
        """ Close the db """
        transaction.commit()
        self.connection.close()
        # In the future we should try to pack based on time
        self.db.pack
        self.db.close()

__database__ = Database()
