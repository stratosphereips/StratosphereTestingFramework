import ZODB.config
import persistent
import transaction
import time
from datetime import datetime

from stf.core.configuration import __configuration__
from stf.common.out import *
from stf.core.dataset import __datasets__
from stf.core.connections import  __group_of_group_of_connections__
from stf.core.models import __groupofgroupofmodels__
from stf.core.notes import __notes__
from stf.core.labels import __group_of_labels__ 

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

        # Labels
        try:
            __group_of_labels__.labels = self.root['labels']
        except KeyError:
            self.root['labels'] = __group_of_labels__.labels


    def has_structure(self, structure_name):
        """ This method searches for a structure in the db"""
        for structure in self.root:
            if structure == structure_name:
                return True
        return False

    def get_new_structure(self, structure):
        """ Given a structure, set the main dict from the db """
        name = str(structure.get_name())
        return self.root[name] 

    def get_structures(self):
        """ get all the structures """
        return self.root

    def set_new_structure(self, structure):
        """ 
        This method takes an object from a new structure (typically from a module) and keeps record of it in the database. 
        A strcture is the main object from the module that we want to store in the db. Actually we store its main dict.
        """
        try:
            name = structure.get_name()
        except AttributeError:
            print_error('The new registered structure does not implement get_name()')
            return False
        try:
            main_dict = structure.get_main_dict()
            print_info('Registering structure name: {}'.format(name))
            self.root[name] = main_dict
            return True
        except AttributeError:
            print_error('The structure does not implement get_main_dict()')
            return False

    def list(self):
        #for structure in self.root:
        #    print_info('Amount of {} in the DB so far: {}'.format(structure, len(self.root[structure])))
        pass

    def delete_structure(self, structure_name):
        """ Delete a structure from the db """
        try:
            structure = self.root[structure_name]
            print_warning('Are you sure you want to delete the structure {} from the db? (YES/NO)'.format(structure_name))
            input = raw_input()
            if input == "YES":
                self.root.pop(structure_name)
                print_info('Structure {} deleted from the db'.format(structure_name))
        except KeyError:
            print_error('No Structure name available.')

    def list_structures(self):
        for structure in self.root:
            print_info('Structure: {}. Amount of objects in db: {}'.format(structure, len(self.root[structure])))

    def close(self):
        """ Close the db """
        transaction.commit()
        self.connection.close()
        # In the future we should try to pack based on time
        self.db.pack
        self.db.close()

    def info(self):
        """ Info about the database"""
        print_warning('Info about the root object of the database')
        print_info('Main Branch | Len')
        for mainbranches in self.root.keys():
            print('\t{:12} | {}'.format(mainbranches, len(self.root[mainbranches])))
        print_info('_p_changed (the persistent state of the object): {}'.format(self.root._p_changed))
        print('\t-> None: The object is a ghost.\n\t-> False but not None: The object is saved (or has never been saved).\n\t-> True: The object has been modified since it was last saved.')
        print_info('_p_state (object persistent state token): {}'.format('GHOST' if self.root._p_state == -1 else 'UPTODATE' if self.root._p_state == 0 else 'CHANGED' if self.root._p_state == 1 else 'STICKY'))
        print_info('_p_jar: {}'.format(self.root._p_jar))
        print_info('_p_oid (persistent object id): {}'.format(self.root._p_oid))
        print
        print_warning('Info about the database object ')
        print_info('Database Name: {}.'.format(self.db.getName()))
        print_info('Database Size: {} B ({} MB).'.format(self.db.getSize(), self.db.getSize()/1024/1024))
        print_info('Object Count: {}.'.format(self.db.objectCount()))
        print_info('Connection debug info: {}.'.format(self.db.connectionDebugInfo()))
        print_info('Cache details:')
        for detail in self.db.cacheDetail():
            print_info('\t{}'.format(detail))

    def revert(self):
        """ revert the connection of the database to the previous state before the last pack"""
        question=raw_input('Warning, this command sync the database on disk with the information on memory. Effectively erasing the changes that were not committed and bringing the new information committed by other instances. \n YES or NO?:')
        if question == 'YES':
            self.connection.sync()
        else:
            print_error('Not reverting.')

    def pack(self):
        """ Pack the database """
        self.db.pack()

    def commit(self):
        """ Commit the changes in the connection to the database """
        import transaction
        transaction.commit()





__database__ = Database()
