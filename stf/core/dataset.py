# This file was partially taken from Viper 
# See the file 'LICENSE' for copying permission.

import time
import datetime
import persistent
import BTrees.OOBTree
import transaction

from stf.common.out import *


class Dataset(object):
    """
    The Dataset class.
    """
    def __init__(self, id):
        self.id = id 
        self.name = None
        # Timestamp of the creation of the session.
        self.created_at = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name
    
    def get_ctime(self):
        return self.created_at
    
    def is_current(self):
        return self.is_current

    def set_name(self,name):
        self.name = name

    def __repr__(self):
        return (' > Dataset id {}, and name {}.'.format(self.id, self.name))


class Datasets(persistent.Persistent):
    def __init__(self):
        self.current = None
        print_info('Creating the Dataset object')
        #self.experiments = BTrees.OOBTree.BTree()
        # The main dictionary of datasets objects using its id as index
        self.datasets = {}

    def delete(self, value):
        try:
            id = int(value)
            self.datasets.pop(id)
            print_info("Deleted dataset #{0}".format(id))
        except ValueError:
            print_info('You should give an dataset id')
        except KeyError:
            print_info('Dataset ID non existant.')


    def create(self,name):
        """ Create a dataset """
        # Move the id
        try:
            # Get the id of the last dataset in the database
            dat_id = self.datasets[self.datasets.keys()[-1]].get_id() + 1
        except (KeyError, IndexError):
            dat_id = 0
        
        # Create the dataset object
        dataset = Dataset(dat_id)
        # Give it a name
        dataset.set_name(name)
        # Add new dataset to the dict
        self.datasets[dataset.get_id()] = dataset
        print_info("Dataset {} created with id {}.".format(name, dataset.get_id()))


    def list_all(self):
        """ Return a vector with all the datasets """
        return self.datasets.values()

    def length(self):
        """ Return the length of the dict """
        return len(self.datasets)

    def is_set(self):
        """ Does the dict exists?"""
        if self.datasets:
            return True
        else:
            return False

__datasets__ = Datasets()
