# This file was partially taken from Viper 
# See the file 'LICENSE' for copying permission.

import time
import datetime
import persistent
import BTrees.IOBTree
import transaction
import os
from subprocess import Popen,PIPE

from stf.common.out import *
from stf.core.file import File
from stf.core.notes import __notes__


###########################
###########################
###########################
class Dataset(persistent.Persistent):
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
        # This dict holds all the groups of models related with this dataset. There can be many because there are several models constructors. Is a dict only to search faster.
        self.group_of_models = {}
        # This stores the id of the group of connections related with this dataset. Only one group of connections is related.
        self.group_of_connections_id = False

    def get_file_type(self,type):
        """ Return the file with type x in this dataset"""
        for file in __datasets__.current.get_files():
            if file.get_type() == type:
                return file
        return False

    def get_files(self):
        """ Return the vector of files of the dataset"""
        return self.files.values()

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
        try:
            return self.files[0]
        except KeyError:
            print_error('There is no main file in this dataset!')
            return False

    def del_file(self,fileid):
        """ Delete a file from the dataset"""
        print_info('File {} with id {} deleted from dataset {}'.format(self.files[fileid].get_name(), self.files[fileid].get_id(), self.get_name() ))
        self.files.pop(fileid)
        # If this was the last file in the dataset, delete the dataset
        if len(self.files) == 0:
            __datasets__.delete(__datasets__.current.get_id())


    def add_file(self,filename):
        """ Add a file to this dataset. """
        # Check that the file exists 
        if not os.path.exists(filename) or not os.path.isfile(filename):
            print_error('File not found: {}'.format(filename))
            return
        # We should have only one file per type
        short_name = os.path.split(filename)[1]
        extension = short_name.split('.')[-1]
        # search for the extensions of the files in the dataset
        for file in self.files:
            if extension in self.files[file].get_type():
                print_error('Only one type of file per dataset is allowed.')
                return False
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

    def get_folder(self):
        return self.folder 

    def set_folder(self, folder):
        self.folder = folder

    def list_files(self):
        rows = []
        for file in self.files.values():
                #rows.append([file.get_short_name(), file.get_id() , file.get_modificationtime(), file.get_size_in_megabytes(), file.get_duration(), file.get_type()])
                rows.append([file.get_short_name(), file.get_id() , file.get_modificationtime(), file.get_size_in_megabytes(), file.get_type()])

        #print(table(header=['File Name', 'Id', 'Creation Time', 'Size', 'Duration', 'Type'], rows=rows))
        print(table(header=['File Name', 'Id', 'Creation Time', 'Size', 'Type'], rows=rows))

    def info_about_file(self,file_id):
        file = self.files[int(file_id)]
        file.info()

    def generate_biargus(self):
        """ Generate the biargus file from the pcap. We know that there is a pcap in the dataset"""
        print_info('Generating the biargus file.')
        pcap_file_name = self.get_file_type('pcap').get_name()
        pcap_file_name_without_extension = '.'.join(pcap_file_name.split('.')[:-1]) 
        biargus_file_name = pcap_file_name_without_extension + '.biargus'
        argus_path = Popen('bash -i -c "type argus"', shell=True, stdin=PIPE, stdout=PIPE).communicate()[0].split()[0]
        if argus_path:
            # If an .biargus file already exist, we must delete it because argus appends the output
            (data, error) = Popen('rm -rf '+biargus_file_name, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()
            (argus_data,argus_error) = Popen('argus -F ./confs/argus.conf -r '+pcap_file_name+' -w '+biargus_file_name, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()
            if not argus_error:
                # Add the new biargus file to the dataset
                self.add_file(biargus_file_name)
            else:
                print_error('There was an error with argus.')
                return False
            return True
        else:
            print_error('argus is not installed. We can not generate the flow files. Download and install from http://qosient.com/argus/dev/argus-clients-latest.tar.gz and http://qosient.com/argus/dev/argus-latest.tar.gz')
            return False

    def generate_binetflow(self):
        """ Generate the binetflow file from the biargus. We know that there is a biargus in the dataset"""
        print_info('Generating the binetflow file.')
        try:
            biargus_file_name = self.get_file_type('biargus').get_name()
        except AttributeError:
            print_error('Can not generate the biargus file. Maybe we don\'t have permisions in the file or folder?')
            return False
        biargus_file_name_without_extension = '.'.join(biargus_file_name.split('.')[:-1]) 
        binetflow_file_name = biargus_file_name_without_extension + '.binetflow'
        ra_path = Popen('bash -i -c "type ra"', shell=True, stdin=PIPE, stdout=PIPE).communicate()[0].split()[0]
        if ra_path:
            (ra_data,ra_error) = Popen('ra -F ./confs/ra.conf -n -Z b -r '+biargus_file_name+' > '+binetflow_file_name, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()
            if not ra_error:
                # Add the new biargus file to the dataset
                self.add_file(binetflow_file_name)
            else:
                print_error('There was an error with ra.')
                return False
            return True
        else:
            print_error('ra is not installed. We can not generate the flow files. Download and install from http://qosient.com/argus/dev/argus-clients-latest.tar.gz and http://qosient.com/argus/dev/argus-latest.tar.gz')
            return False


    def __repr__(self):
        return (' > Dataset id {}, and name {}.'.format(self.id, self.name))

    def add_group_of_models(self, group_of_models_id):
        """ Add the group of models id to the list of groups of models related with this dataset """
        self.group_of_models[group_of_models_id] = None

    def get_group_of_models(self):
        return self.group_of_models

    def has_group_of_models(self,group_of_models_id):
        return self.group_of_models.has_key(group_of_models_id)
    
    def add_group_of_connections_id(self, group_of_connections_id):
        """ Add the group of connections that is related to this dataset. Is only one, but we store it this way. """
        self.group_of_connections_id = group_of_connections_id

    def remove_group_of_connections_id(self, group_of_connections_id):
        self.group_of_connections_id = False

    def get_group_of_connections_id(self):
        try:
            return self.group_of_connections_id
        except AttributeError:
            return False

    def set_group_of_connections_id(self, group_of_connections_id):
        self.group_of_connections_id = group_of_connections_id

    def set_note_id(self, note_id):
        self.note_id = note_id

    def edit_note(self):
        """ Edit the note related with this dataset or create a new one and edit it """
        try:
            note_id = self.note_id
            __notes__.edit_note(note_id)
        except AttributeError:
            self.note_id = __notes__.new_note()
            __notes__.edit_note(self.note_id)

    def del_note(self):
        """ Delete the note related with this dataset """
        try:
            # First delete the note
            note_id = self.note_id
            __notes__.del_note(note_id)
            # Then delete the reference to the note
            del self.note_id 

        except AttributeError:
            print_error('No such note id exists.')

    def get_note_id(self):
        """ Return the note id or false """
        try:
            return self.note_id
        except AttributeError:
            return False




###########################
###########################
###########################
class Datasets(persistent.Persistent):
    def __init__(self):
        self.current = False
        # The main dictionary of datasets objects using its id as index
        self.datasets = BTrees.IOBTree.BTree()

    def get_datasets_ids(self):
        """ Return the ids of the datasets """
        return self.datasets.keys()

    def get_dataset(self, id):
        """ Return a dataset objet given the id """
        try:
            return self.datasets[id]
        except:
            print_error('No such dataset id')
            return False

    def delete(self, dataset_id): 
        """ Delete a dataset from the list of datasets """
        # Before deleting the dataset, delete the connections
        from stf.core.connections import __group_of_group_of_connections__
        __group_of_group_of_connections__.delete_group_of_connections(dataset_id)
        # Before deleting the dataset, delete the models
        from stf.core.models import __groupofgroupofmodels__
        __groupofgroupofmodels__.delete_group_of_models_with_dataset_id(dataset_id)

        try:
            # Now delete the dataset
            self.datasets.pop(dataset_id)
            print_info("Deleted dataset #{0}".format(dataset_id))
            # If it was the current dataset, we have no current
            if self.current and self.current.get_id() == dataset_id:
                self.current = False
        except ValueError:
            print_info('You should give an dataset id')
        except KeyError:
            print_info('Dataset ID non existant.')

    def add_file(self, filename):
        """ Add a new file to the current dataset"""
        if self.current:
            # Check that the file exists 
            if not os.path.exists(filename) or not os.path.isfile(filename):
                print_error('File not found: {}'.format(filename))
                return
            # Add this file to the dataset
            self.current.add_file(filename)
        else:
            print_error('No dataset selected. Use -s option.')

    def del_file(self,fileid):
        """ Delete a file to the current dataset"""
        if self.current:
            # Delete this file from the dataset
            self.current.del_file(int(fileid))

        else:
            print_error('No dataset selected. Use -s option.')

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
        name = raw_input('The name of the dataset or \'Enter\' to use the name of the last folder:')
        if not name:
            name = os.path.split(filename)[0].split('/')[-1]

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
        self.current = dataset

    def list(self):
        """ List all the datasets """
        print_info("Datasets Available:")
        rows = []
        for dataset in self.datasets.values():
                main_file = dataset.get_main_file()
                rows.append([dataset.get_name(), dataset.get_id() , dataset.get_atime() , main_file.get_short_name(), main_file.get_modificationtime(), dataset.get_folder(), True if (self.current and self.current.get_id() == dataset.get_id()) else False, dataset.get_note_id() if dataset.get_note_id() >= 0 else '' ])
        print(table(header=['Dataset Name', 'Id', 'Added Time', 'Main File Name', 'Main File Creation Time', 'Folder', 'Current', 'Note'], rows=rows))

    def list_files(self):
        """ List all the files in dataset """
        if self.current:
            print_info('Getting information about the files... please wait')
            print_info('Files Available in Dataset {}:'.format(self.current.get_name()))
            self.current.list_files()
        else:
            print_error('No dataset selected. Use -s option.')

    def info_about_file(self,file_id):
        """ Give info about a specific file in a dataset"""
        if self.current:
            try:
                self.current.info_about_file(int(file_id))
            except (KeyError, UnboundLocalError):
                print_info('No such file id')
        else:
            print_error('No dataset selected. Use -s option.')

    def length(self):
        """ Return the length of the dict """
        return len(self.datasets)

    def is_set(self):
        """ Does the dict exists?"""
        if self.datasets:
            return True
        else:
            return False

    def unselect_current(self):
        """ UnSelects the current dataset"""
        self.current = False

    def select(self,dataset_id):
        """ Selects a dataset as current to enable other more specific commands"""
        try:
            self.current = self.datasets[int(dataset_id)]
            print_info('The current dataset is {} with id {}'.format(self.current.get_name(), self.current.get_id()))
        except KeyError:
            print_error('No such dataset id')

    def generate_argus_files(self):
        """ Generate the biargus and binetflow files"""
        if self.current:
            # Do we have a binetflow file in the dataset?
            binetflow_in_dataset = self.current.get_file_type('binetflow')
            # Do we have a binetflow file in the folder?
            # Do we have a biargus file in the dataset?
            biargus_in_dataset = self.current.get_file_type('biargus')
            # Do we have a biargus file in the folder?

            # Do we have a pcap file in the dataset?
            pcap_in_dataset = self.current.get_file_type('pcap')

            if binetflow_in_dataset:
                # Ask if we should regenerate
                pass
            elif biargus_in_dataset:
                # We should generate the binetflow
                # Or regenerate
                self.current.generate_binetflow()
            elif pcap_in_dataset:
                # We should generate the biargus and the binetflow
                self.current.generate_biargus()
                self.current.generate_binetflow()
            else:
                print_error('At least a pcap file should be in the dataset.')

            # Do we have a pcap file in the folder?
        else:
            print_error('No dataset selected. Use -s option.')

    def edit_note(self, dataset_id):
        """ Get a dataset id and edit its note """
        try:
            dataset = self.datasets[int(dataset_id)]
            dataset.edit_note()
        except KeyError:
            print_error('No such dataset id.')

    def del_note(self, dataset_id):
        """ Get a dataset id and delete its note """
        try:
            dataset = self.datasets[int(dataset_id)]
            dataset.del_note()
        except KeyError:
            print_error('No such dataset id.')


__datasets__ = Datasets()
