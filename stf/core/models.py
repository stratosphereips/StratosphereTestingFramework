import persistent
import BTrees.OOBTree

from stf.common.out import *
from stf.core.dataset import __datasets__
from stf.core.connections import  __group_of_group_of_connections__
from stf.core.models_constructors import __modelsconstructors__ 

class Model(object):
    """
    The Model
    """
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def add_flow(self,flow):
        """ Get a flow and generate a state to store"""
        pass

    def set_constructor(self,constructor):
        self.constructor = constructor


class Group_of_Models(object):
    def __init__(self, id):
        """ This class holds all the models for a dataset"""
        self.id = id
        self.models = BTrees.OOBTree.BTree()

    def get_models(self):
        return self.models.values()

    def get_id(self):
        return self.id

    def generate_models(self):
        """ Generate all the individual models. We are related with only one dataset and connection group. """
        # Get the group of connections with our id
        group_of_connections = __group_of_group_of_connections__.get_group(self.id)

        # For each connection
        for connection in group_of_connections.get_connections():
            # Create its model
            model_id = connection.get_id()
            new_model = Model(model_id)
            # Set the constructor for this model. Each model has a specific way of constructing the states
            new_model.set_constructor(__modelsconstructors__.get_default_constructor())
            for flow in connection.get_flows():
                new_model.add_flow(flow)
            self.models[model_id] = new_model


class Group_of_Group_of_Models(persistent.Persistent):
    def __init__(self):
        """ This class holds all the groups of models"""
        self.group_of_models = BTrees.OOBTree.BTree()

    def list_groups(self):
        if __datasets__.current:
            print_info('Groups of Models in the dataset')
            rows = []
            for group in self.group_of_models.values():
                if group.get_id() == __datasets__.current.get_id():
                    rows.append([group.get_id(), len(group.get_models())])
            print(table(header=['Group of Model Id', 'Amount of Models'], rows=rows))
        else:
            print_error('You should select a dataset first.')
            return False

    def generate_group_of_models(self):
        # Get the id for the current dataset
        dataset_id = __datasets__.current.get_id()
        # This is the same id for the group_of_connections
        group_of_connections_id = dataset_id

        # Do we have the group of models for this id?
        try:
            group_of_models = self.group_of_models[group_of_connections_id]
        except KeyError:
            # First time
            group_of_models = Group_of_Models(group_of_connections_id)
            self.group_of_models[group_of_connections_id] = group_of_models

        # Generate the models
        group_of_models.generate_models()


__groupofgroupofmodels__ = Group_of_Group_of_Models()
