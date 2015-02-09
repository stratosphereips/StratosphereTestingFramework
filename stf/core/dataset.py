# This file was partially taken from Viper 
# See the file 'LICENSE' for copying permission.

import time
import datetime
import persistent
import BTrees.OOBTree
import transaction
import os

from stf.common.out import *
from stf.core.file import File


class Dataset(object):
    """
    The Dataset class.
    """
    def __init__(self, id):
        self.id = id 
        self.name = None
        # Timestamp of the creation of the session.
        self.added_on = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        self.ctime = None
        # Dict of files related to this dataset
        self.files = {}
        # Foler that holds all the files for this dataset
        self.folder = None

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

    def get_main_file(self):
        """ Returns the name of the first file used to create the dataset. Usually the only one"""
        return self.files[0]

    def add_file(self,filename):
        """ Add a file to this dataset. """
        # Check that the file exists 
        if not os.path.exists(filename) or not os.path.isfile(filename):
            print_error('File not found: {}'.format(filename))
            return

        # Get the new id for this file
        try:
            # Get the id of the last file in the dataset
            f_id = self.files[list(self.files.keys())[-1]].get_id() + 1
        except (KeyError, IndexError):
            f_id = 0

        # Create the file object
        f = File(filename, f_id)
        # Add it to the list of files related to this dataset
        self.files[f_id] = f

        print_info('Added file {} to dataset {}'.format(filename, self.name))


    def del_file(self,value):
        """ To delete a file associated with the datase. By id or name """
        pass

    def get_folder(self):
        return self.folder 

    def set_folder(self, folder):
        self.folder = folder

    def list_files(self):
        rows = []
        for file in self.files.values():
                rows.append([file.get_short_name(), file.get_id() , file.get_modificationtime(), file.get_size_in_megabytes(), file.get_duration()])

        print(table(header=['File Name', 'Id', 'Creation Time', 'Size', 'Duration'], rows=rows))

    def info_about_file(self,file_id):
        file = self.files[int(file_id)]
        file.info()

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


    def create(self,filename):
        """ Create a new dataset from a file name"""

        # Check that the file exists 
        if not os.path.exists(filename) or not os.path.isfile(filename):
            print_error('File not found: {}'.format(filename))
            return

        # Get the new id for this dataset
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

        # Add this file to the dataset
        dataset.add_file(filename)

        # Store the folder of this dataset
        folder = os.path.split(filename)[0]
        dataset.set_folder(folder)

        # Add th enew dataset to the dict
        self.datasets[dataset.get_id()] = dataset
        print_info("Dataset {} added with id {}.".format(name, dataset.get_id()))


    def list(self):
        """ List all the datasets """
        print_info("Datasets Available:")
        rows = []
        for dataset in self.datasets.values():
                main_file = dataset.get_main_file()
                rows.append([dataset.get_name(), dataset.get_id() , dataset.get_atime() , main_file.get_short_name(), main_file.get_modificationtime(), dataset.get_folder()])

        print(table(header=['Dataset Name', 'Id', 'Added Time', 'Main File Name', 'Main File Creation Time', 'Folder'], rows=rows))

    def list_files(self, dataset_id):
        """ List all the files in dataset """
        try:
            dataset = self.datasets[int(dataset_id)]
        except KeyError:
            print_info('No such dataset id')
            return
        print_info('Files Available in Dataset {}:'.format(dataset.get_name()))
        dataset.list_files()

    def info_about_file(self, dataset_id, file_id):
        """ Give info about a specific file in a dataset"""
        try:
            dataset = self.datasets[int(dataset_id)]
        except (KeyError, UnboundLocalError):
            print_info('No such dataset id')
        try:
            dataset.info_about_file(int(file_id))
        except (KeyError, UnboundLocalError):
            print_info('No such file id')



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
