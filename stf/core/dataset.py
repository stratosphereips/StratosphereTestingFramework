# This file was partially taken from Viper 
# See the file 'LICENSE' for copying permission.

import time
import datetime
import persistent
import BTrees.OOBTree
import transaction
import os

from stf.common.out import *


class Dataset(object):
    """
    The Dataset class.
    """
    def __init__(self, id):
        self.id = id 
        self.name = None
        # Timestamp of the creation of the session.
        self.added_on = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        self.filename = None
        self.ctime = None

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name
    
    def get_atime(self):
        return self.added_on
    
    def is_current(self):
        return self.is_current

    def set_name(self,name):
        self.name = name

    def set_filename(self,filename):
        self.filename = filename

    def get_filename(self):
        return self.filename 

    def set_creationtime(self,ctime):
        self.ctime = ctime

    def get_creationtime(self):
        return self.ctime 

    def __repr__(self):
        return (' > Dataset id {}, and name {}.'.format(self.id, self.name))


class Datasets(persistent.Persistent):
    def __init__(self):
        self.current = None
        print_info('Creating the Dataset object')
        self.datasets = BTrees.OOBTree.BTree()
        # The main dictionary of datasets objects using its id as index
        #self.datasets = {}

    def delete(self, value):
        try:
            id = int(value)
            self.datasets.pop(id)
            print_info("Deleted dataset #{0}".format(id))
        except ValueError:
            print_info('You should give an dataset id')
        except KeyError:
            print_info('Dataset ID non existant.')


    def add(self,filename):
        """ Add a dataset from a file name"""

        # Check that the file exists and is not empty and we can read it
        #print_info(filename)
        if not os.path.exists(filename) or not os.path.isfile(filename):
            print_error('File not found: {}'.format(filename))
            return


        # Get the new id 
        try:
            # Get the id of the last dataset in the database
            dat_id = self.datasets[list(self.datasets.keys())[-1]].get_id() + 1
        except (KeyError, IndexError):
            dat_id = 0
       

        # Create the dataset object
        dataset = Dataset(dat_id)

        # Ask for a dataset name or default to the file name
        name = raw_input('Enter the name of the dataset or Enter to use file name as name:')
        if not name:
            name = os.path.split(filename)[1]

        # Set the name
        dataset.set_name(name)

        # Set the filename
        dataset.set_filename(filename)

        # Set the creation time
        ctime = time.ctime(os.path.getctime(filename))
        dataset.set_creationtime(ctime)



        # Add new dataset to the dict
        self.datasets[dataset.get_id()] = dataset
        print_info("Dataset {} added with id {}.".format(name, dataset.get_id()))


    def list(self):
        """ List all the datasets """
        print_info("Datasets Available:")
        rows = []
        for dataset in self.datasets.values():
                rows.append([dataset.get_name(), dataset.get_id() , dataset.get_atime() , dataset.get_filename(), dataset.get_creationtime()])

        print(table(header=['Dataset Name', 'Id', 'Added Time', 'File Name', 'Dataset Creation Time'], rows=rows))

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
