import persistent
import BTrees.OOBTree
import re

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
        self.state = ''

    def get_id(self):
        return self.id

    def add_flow(self,flow):
        """ Get a flow and generate a state to store"""
        self.state += self.constructor.get_state(flow, self.get_id())

    def set_constructor(self,constructor):
        """ Set the constructor of the model"""
        self.constructor = constructor

    def get_state(self):
        return self.state


class Group_of_Models(object):
    def __init__(self, id):
        """ This class holds all the models for a dataset"""
        self.id = id
        self.models = BTrees.OOBTree.BTree()

    def get_models(self):
        return self.models.values()

    def get_model(self,id):
        return self.models[id]

    def get_id(self):
        return self.id

    def generate_models(self):
        """ Generate all the individual models. We are related with only one dataset and connection group. """
        # Get the group of connections with our id
        group_of_connections = __group_of_group_of_connections__.get_group(self.id)

        if group_of_connections:
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
        else:
            print_error('There is no group of connections to generate the models from. First generate the connections for this dataset.')

    def construct_filter(self,tempfilter):
        """ Get the filter string and decode all the operations """
        # If the filter string is empty, delete the filter variable
        if not tempfilter:
            try:
                del self.filter 
            except:
                pass
            return True
        self.filter = {}
        # Get the individual parts. We only support and's now.
        filter = tempfilter.strip("\"") 
        parts_of_filter = re.split('and',filter)
        for part in parts_of_filter:
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
        try:
            self.filter
            for filter_key in self.filter:
                operator = self.filter[filter_key][0]
                value = self.filter[filter_key][1]
                if filter_key == 'statelength':
                    state = model.get_state()
                    if operator == '<':
                        if len(state) < int(value):
                            return True
                    elif operator == '>':
                        if len(state) > int(value):
                            return True
                    elif operator == '=':
                        if len(state) == int(value):
                            return True
            return False
        except AttributeError:
            # If we don't have any filter string, just return true and show everything
            return True

    def list_models(self, filter_string=''):
        rows = []
        # set the filter
        self.construct_filter(filter_string)
        amount = 0
        print('| Model Id | State |')
        for model in self.models.values():
            if self.apply_filter(model):
                print_row([model.get_id(), model.get_state()])
                amount += 1
        print_info('Amount of modules printed: {}'.format(amount))

    def delete_model_by_id(self,id):
        try:
            self.models.pop(id)
            print_info('Model {} deleted from the group.'.format(id))
        except KeyError:
            print_error('That model does not exists.')

    def delete_model_by_filter(self,filter_string):
        try:
            # set the filter
            self.construct_filter(filter_string)
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


    def count_models(self, filter_string=''):
        rows = []
        # set the filter
        self.construct_filter(filter_string)
        amount = 0
        for model in self.models.values():
            if self.apply_filter(model):
                amount += 1
        print_info('Amount of modules filtered: {}'.format(amount))



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
                if group.get_id() == __datasets__.current.get_id():
                    rows.append([group.get_id(), len(group.get_models()), __datasets__.current.get_id(), __datasets__.current.get_name() ])
            print(table(header=['Group of Model Id', 'Amount of Models', 'Dataset Id', 'Dataset Name'], rows=rows))
        # Otherwise print them all
        else:
            rows = []
            for group in self.group_of_models.values():
                dataset = __datasets__.get_dataset(group.get_id())
                rows.append([group.get_id(), len(group.get_models()), dataset.get_id(), dataset.get_name() ])
            print(table(header=['Group of Model Id', 'Amount of Models', 'Dataset Id', 'Dataset Name'], rows=rows))

    def delete_group_of_models(self, id):
        try:
            self.group_of_models.pop(int(id))
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

            # This is the same id for the group_of_models
            group_of_models_id = dataset_id

            # Do we have the group of models for this id?
            try:
                group_of_models = self.group_of_models[group_of_models_id]
            except KeyError:
                # First time
                group_of_models = Group_of_Models(group_of_models_id)
                self.group_of_models[group_of_models_id] = group_of_models

            # Generate the models
            group_of_models.generate_models()
        else:
            print_error('You should select a dataset')

    def list_models_in_group(self,id, filter=''):
        try:
            group = self.group_of_models[int(id)]
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

    def delete_a_model_from_the_group_by_filter(self,filterstring):
        # Get the id of the current dataset
        if __datasets__.current:
            group_id = __datasets__.current.get_id()
            self.group_of_models[group_id].delete_model_by_filter(filterstring)
        else:
            print_error('There is no dataset selected.')

    def count_models_in_group(self,id, filter=''):
        try:
            group = self.group_of_models[int(id)]
            group.count_models(filter)
        except KeyError:
            print_error('No such group of models.')



__groupofgroupofmodels__ = Group_of_Group_of_Models()