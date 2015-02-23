import persistent
import BTrees.OOBTree
import re

from stf.common.out import *
from stf.core.dataset import __datasets__
from stf.core.connections import  __group_of_group_of_connections__
from stf.core.models_constructors import __modelsconstructors__ 

###############################
###############################
###############################
class Model(object):
    """
    The Model
    """
    def __init__(self, id):
        self.id = id
        self.state = ''

    def get_id(self):
        return self.id

    def add_flow(self,flow):
        """ Get a flow and generate a state to store"""
        self.state += self.constructor.get_state(flow, self.get_id())

    def set_constructor(self,constructor):
        """ Set the constructor of the model"""
        self.constructor = constructor

    def get_constructor(self):
        return self.constructor

    def get_state(self):
        return self.state


###############################
###############################
###############################
class Group_of_Models(object):
    def __init__(self, id):
        """ This class holds all the models for a dataset"""
        self.id = id
        self.models = BTrees.OOBTree.BTree()

    def set_dataset_id(self, dataset_id):
        self.dataset_id = dataset_id

    def get_dataset_id(self):
        return self.dataset_id 

    def set_group_connection_id(self, group_connection_id):
        """ Receives the id of the group of connections that this group of models is related to """
        self.group_connection_id = group_connection_id

    def get_group_connection_id(self):
        return self.group_connection_id

    def get_models(self):
        return self.models.values()

    def get_model(self,id):
        return self.models[id]

    def get_id(self):
        return self.id

    def generate_models(self):
        """ Generate all the individual models. We are related with only one dataset and connection group. """
        # Get the group of connections from the id
        group_of_connections = __group_of_group_of_connections__.get_group(self.get_group_connection_id())

        # For each connection
        for connection in group_of_connections.get_connections():
            # Create its model. Remember that the connection id and the model id is the 4-tuple
            model_id = connection.get_id()
            new_model = Model(model_id)
            # Set the constructor for this model. Each model has a specific way of constructing the states
            new_model.set_constructor(__modelsconstructors__.get_default_constructor())
            for flow in connection.get_flows():
                new_model.add_flow(flow)
            self.models[model_id] = new_model

    def construct_filter(self,filter):
        """ Get the filter string and decode all the operations """
        # If the filter string is empty, delete the filter variable
        if not filter:
            try:
                del self.filter 
            except:
                pass
            return True
        self.filter = {}
        # Get the individual parts. We only support and's now.
        for part in filter:
            # Get the key
            try:
                key = re.split('<|>|=', part)[0]
                value = re.split('<|>|=', part)[1]
            except IndexError:
                # No < or > or = in the string. Just stop.
                break
            try:
                part.index('<')
                operator = '<'
            except ValueError:
                pass
            try:
                part.index('>')
                operator = '>'
            except ValueError:
                pass
            try:
                part.index('=')
                operator = '='
            except ValueError:
                pass
            self.filter[key] = (operator, value)

    def apply_filter(self,model):
        """ Use the stored filter to know what we should match"""
        responses = {}
        try:
            self.filter
            for filter_key in self.filter:
                operator = self.filter[filter_key][0]
                value = self.filter[filter_key][1]
                if filter_key == 'statelength':
                    state = model.get_state()
                    if operator == '<':
                        if len(state) < int(value):
                            responses['statelength'] = True
                        else:
                            responses['statelength'] = False
                    elif operator == '>':
                        if len(state) > int(value):
                            responses['statelength'] = True
                        else:
                            responses['statelength'] = False
                    elif operator == '=':
                        if len(state) == int(value):
                            responses['statelength'] = True
                        else:
                            responses['statelength'] = False
                elif filter_key == 'nameincludes':
                    name = model.get_id()
                    if operator == '=':
                        if value in name:
                            responses['nameincludes'] = True
                        else:
                            responses['nameincludes'] = False

            for response in responses:
                if not responses[response]:
                    return False
            return True
        except AttributeError:
            # If we don't have any filter string, just return true and show everything
            return True

    def list_models(self, filter=''):
        rows = []
        # set the filter
        self.construct_filter(filter)
        amount = 0
        print('| Model Id | State |')
        for model in self.models.values():
            if self.apply_filter(model):
                print_row([model.get_id(), model.get_state()])
                amount += 1
        print_info('Amount of modules printed: {}'.format(amount))

    def delete_model_by_id(self,id):
        try:
            # Now delete the group
            self.models.pop(id)
        except KeyError:
            print_error('That model does not exists.')

    def delete_model_by_filter(self,filter):
        """ Delete the models using the filter. Do not delete the related connections """
        try:
            # set the filter
            self.construct_filter(filter)
            amount = 0
            ids_to_delete = []
            for model in self.models.values():
                if self.apply_filter(model):
                    ids_to_delete.append(model.get_id())
                    amount += 1
        
            # We should delete the models AFTER finding them, if not, for some reason the following model after a match is missed.
            for id in ids_to_delete:
                self.models.pop(id)

            print_info('Amount of modules deleted: {}'.format(amount))
        except:
            print_error('An error ocurred while deleting models by filter.')


    def count_models(self, filter=''):
        rows = []
        # set the filter
        self.construct_filter(filter)
        amount = 0
        for model in self.models.values():
            if self.apply_filter(model):
                amount += 1
        print_info('Amount of modules filtered: {}'.format(amount))


###############################
###############################
###############################
class Group_of_Group_of_Models(persistent.Persistent):
    def __init__(self):
        """ This class holds all the groups of models"""
        self.group_of_models = BTrees.OOBTree.BTree()

    def list_groups(self):
        print_info('Groups of Models')
        # If we selected a dataset, just print the one belonging to the dataset
        if __datasets__.current:
            rows = []
            for group in self.group_of_models.values():
                if group.get_dataset_id() == __datasets__.current.get_id():
                    rows.append([group.get_id(), len(group.get_models()), __datasets__.current.get_id(), __datasets__.current.get_name() ])
            print(table(header=['Group of Model Id', 'Amount of Models', 'Dataset Id', 'Dataset Name'], rows=rows))
        # Otherwise print them all
        else:
            rows = []
            for group in self.group_of_models.values():
                # Get the dataset based on the dataset id stored from this group 
                dataset = __datasets__.get_dataset(group.get_dataset_id())
                rows.append([group.get_id(), len(group.get_models()), dataset.get_id(), dataset.get_name() ])
            print(table(header=['Group of Model Id', 'Amount of Models', 'Dataset Id', 'Dataset Name'], rows=rows))

    def delete_group_of_models(self, id):
        try:
            # First delete all the the models in the group
            group = self.group_of_models[id]
            amount = 0
            for model in group.get_models():
                model_id = model.get_id()
                group.delete_model_by_id(model_id)
                amount += 1
            print_info('Deleted {} models inside the group'.format(amount))

            # Now delete the model
            self.group_of_models.pop(id)
            print_info('Deleted group of models with id {}'.format(id))
        except KeyError:
            print_error('That group of models does not exists.')

    def generate_group_of_models(self):
        if __datasets__.current:
            # Get the id for the current dataset
            dataset_id = __datasets__.current.get_id()
            # We should check that there is a group of connections already for this dataset
            if not __group_of_group_of_connections__.get_group(dataset_id):
                # There are not group of connections for this dataset, just generate it
                print_info('There were no connections for this dataset. Generate them first.')
                return False

            # Get the id of the groups of connections these models are related to
            group_connection = __group_of_group_of_connections__.get_group(dataset_id)
            if group_connection:
                group_connection_id = group_connection.get_id()
            else:
                print_error('There are no connections for this dataset yet. Please generate them.')

            # The id of this group of models is the id of the dataset + the id of the model constructor. Because we can have the same connnections modeled by different constructors.
            group_of_models_id = str(dataset_id) + '-' + str(__modelsconstructors__.get_default_constructor().get_id())

            # Do we have the group of models for this id?
            try:
                group_of_models = self.group_of_models[group_of_models_id]
            except KeyError:
                # First time.
                # Create the group of models
                group_of_models = Group_of_Models(group_of_models_id)
                # Set the group of connections they will be using
                group_of_models.set_group_connection_id(group_connection_id)
                # Set the dataset id for this group of models
                group_of_models.set_dataset_id(dataset_id)
                # Store
                self.group_of_models[group_of_models_id] = group_of_models

            # Generate the models
            group_of_models.generate_models()
        else:
            print_error('There is no dataset selected.')

    def list_models_in_group(self, id, filter=''):
        try:
            group = self.group_of_models[id]
            group.list_models(filter)
        except KeyError:
            print_error('No such group of models.')

    def delete_a_model_from_the_group_by_id(self,id):
        # Get the id of the current dataset
        if __datasets__.current:
            group_id = __datasets__.current.get_id()
            self.group_of_models[group_id].delete_model_by_id(id)
        else:
            print_error('There is no dataset selected.')

    def delete_a_model_from_the_group_by_filter(self,filter=''):
        # Get the id of the current dataset
        if __datasets__.current:
            group_id = __datasets__.current.get_id()
            self.group_of_models[group_id].delete_model_by_filter(filter)
        else:
            print_error('There is no dataset selected.')

    def count_models_in_group(self, id, filter=''):
        try:
            group = self.group_of_models[id]
            group.count_models(filter)
        except KeyError:
            print_error('No such group of models.')



__groupofgroupofmodels__ = Group_of_Group_of_Models()
