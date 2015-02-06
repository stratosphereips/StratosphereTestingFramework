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


class Experiments(persistent.Persistent):
    def __init__(self):
        self.current = None
        #self.experiments = BTrees.OOBTree.BTree()
        self.experiments = {}
        self.exp_id = 0 

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
                for e in self.experiments:
                    if self.experiments[e].get_name() == value:
                        self.current = self.experiments[e]
                        print_info("Switched to experiment {}".format(self.current.get_name()))

    def create(self,name):
        self.exp_id += 1
        experiment = Experiment(self.exp_id)
        experiment.set_name(name)

        # Add new experiment to the list.
        self.experiments[experiment.get_id()] = experiment

        # Mark the new session as the current one.
        self.current = experiment

        print_info("Experiment {} created with id {}.".format(name, experiment.get_id()))


    def list_all(self):
        """ Return a vector with all the experiments """
        return self.experiments.values()

    def length(self):
        return len(self.experiments)

    def is_set(self):
        if self.experiments:
            return True
        else:
            return False


__experiments__ = Experiments()



