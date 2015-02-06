# This file was partially taken from Viper 
# See the file 'LICENSE' for copying permission.

import time
import datetime
import persistent
import BTrees.OOBTree
import transaction

from stf.common.out import *


class Experiment(persistent.Persistent):
    """
    The Experiment class. This will hold all the data related to an experiment.
    """
    def __init__(self, id):
        self.id = id 
        self.name = None
        # Timestamp of the creation of the session.
        self.created_at = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        self._p_changed = True
        transaction.commit()

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
        self._p_changed = True
        transaction.commit()


class Experiments(persistent.Persistent):
    def __init__(self):
        self.current = None
        self.experiments = BTrees.OOBTree.BTree()
        self._p_changed = True
        transaction.commit()

    def is_current(self, experiment_id):
        if self.current == experiment_id:
            return True
        else:
            return False

    def switch_to(self, experiment_id):
        self.current = experiment_id
        self._p_changed = True
        print_info("Switched to experiment #{0}".format(self.current.id))

    def create(self,name):
        total = len(self.experiments)
        experiment = Experiment(total + 1)
        experiment.set_name(name)

        # Add new experiment to the list.
        self.experiments[experiment.get_id()] = experiment
        # Mark the new session as the current one.
        self.current = experiment.get_id()

        print_info("Experiment {} created with id {}.".format(name, experiment.get_id()))

        # Commit
        self._p_changed = True
        transaction.commit()

    def list_all(self):
        """ Return a vector with all the experiments """
        return self.experiments.values()

__experiments__ = Experiments()



