# This file was partially taken from Viper 
# See the file 'LICENSE' for copying permission.

import time
import datetime
import persistent
import BTrees.OOBTree
import transaction

from stf.common.out import *


class Experiment(object):
    """
    The Experiment class. This will hold all the data related to an experiment.
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
        return (' > Experiment id {}, and name {}.'.format(self.id, self.name))


class Experiments(persistent.Persistent):
    def __init__(self):
        self.current = None
        self.experiments = BTrees.OOBTree.BTree()
        # The main dictionary of experiments objects using its id as index
        #self.experiments = {}
        print_info('Creating the Experiments object')

    def is_current(self, experiment_id):
        if self.current == experiment_id:
            return True
        else:
            return False

    def delete(self, value):
        try:
            id = int(value)
            self.experiments.pop(id)
            print_info("Deleted experiment #{0}".format(id))
        except ValueError:
            print_info('You should give an experiment id')
        except KeyError:
            print_info('Experiment ID non existant.')

    def switch_to(self, value):
        try:
            self.current = self.experiments[int(value)]
            print_info("Switched to experiment #{0}".format(self.current.get_id()))
        except ValueError:
            if isinstance(value,str):
                #for e in self.experiments:
                    #if self.experiments[e].get_name() == value:
                        #self.current = self.experiments[e]
                        #print_info("Switched to experiment {}".format(self.current.get_name()))
                for e in self.experiments.values():
                    if e.get_name() == value:
                        self.current = e
                        print_info("Switched to experiment {}".format(self.current.get_name()))




    def create(self,name):
        """ Create an experiment """
        # Move the id
        try:
            # Get the id of the last experiment in the database
            exp_id = self.experiments[list(self.experiments.keys())[-1]].get_id() + 1
        except (KeyError, IndexError):
            exp_id = 0
        
        # Create the experiment object
        experiment = Experiment(exp_id)
        # Give it a name
        experiment.set_name(name)
        # Add new experiment to the dict
        self.experiments[experiment.get_id()] = experiment
        # Mark the new session as the current one.
        self.current = experiment
        print_info("Experiment {} created with id {}.".format(name, experiment.get_id()))


    def list_all(self):
        """ List all the experiments """
        print_info("Experiments Available:")

        rows = []
        for experiment in list(self.experiments.values()):
                rows.append([experiment.get_name(), experiment.get_id() , experiment.get_ctime(), True if (self.current and self.current.get_id() == experiment.get_id()) else False  ])
        print(table(header=['Experiment Name', 'Id', 'Creation Time', 'Current'], rows=rows))

    def length(self):
        """ Return the length of the dict of experiments"""
        return len(self.experiments)

    def is_set(self):
        """ Does the experiment dict exists?"""
        if self.experiments:
            return True
        else:
            return False

__experiments__ = Experiments()
