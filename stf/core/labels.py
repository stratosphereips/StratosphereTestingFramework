# This file was partially taken from Viper 
# See the file 'LICENSE' for copying permission.

import persistent
import BTrees.IOBTree
import transaction
import os
import sys

from stf.common.out import *
from stf.core.dataset import __datasets__
from stf.core.models import __groupofgroupofmodels__


########################
########################
########################
class Label(persistent.Persistent):
    """ A class to manage a single label"""
    def __init__(self,id):
        self.id = id
        self.name = ''
        # This holds all the connections in the label
        self.connections = {}

    def get_id(self):
        return self.id

    def set_id(self, i):
        self.id = id

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def add_connection(self, dataset_id, connection_id):
        """ Receive a dataset_id and a connection_id and store them in this label"""
        try:
            d_id = self.connections[dataset_id]
            self.connections[dataset_id].append(connection_id)
        except KeyError:
            # First time we see this dataset id
            self.connections[dataset_id] = []
            self.connections[dataset_id].append(connection_id)
        
    def delete_connection(self, dataset_id, connection_id):
        """ Delete this connection in this label """
        try:
            for conn in self.connections[dataset_id]:
                if conn == connection_id:
                    self.connections[dataset_id].remove(connection_id)
                    return True
            # We have the dataset_id but not the connection_id
            return False
        except KeyError:
            # We dont have that dataset_id
            return False

    def has_connection(self, dataset_id, connection_id):
        """ Check if we have this connection in this label """
        try:
            for conn in self.connections[dataset_id]:
                if conn == connection_id:
                    return True
            # We have the dataset_id but not the connection_id
            return False
        except KeyError:
            # We dont have that dataset_id
            return False

    def has_dataset(self, dataset_id):
        """ Check if this label has any connection with this dataset_id"""
        try:
            a = self.connections[dataset_id]
            return True
        except KeyError:
            # We dont have that dataset_id
            return False

    def get_datasets(self):
        return self.connections.keys()

    def get_connections(self):
        conns = []
        for dataset in self.connections:
            for con in self.connections[dataset]:
                conns.append(con)
        return conns

    def get_connections_for_dataset(self, dataset_id):
        conns = []
        for con in self.connections[dataset_id]:
            conns.append(con)
        return conns

    def show_models(self):
        """ Show the models in the label"""
        rows = []
        # Get all the unique datasets for this label
        for dataset_id in set(self.get_datasets()):
            # Get all the connections_id on each dataset
            for connection_id in self.get_connections_for_dataset(dataset_id):
                dataset = __datasets__.get_dataset(dataset_id)
                group_of_models = dataset.get_group_of_models()
                # Usually there is only one group of models.. .but just in case there are more
                for group_id in group_of_models:
                    group = __groupofgroupofmodels__.get_group(group_id)
                    for conn in self.connections[dataset_id]:
                        if group.has_model(conn):
                            model = group.get_model(conn)
                            state = model.get_state()
                rows.append([dataset_id, connection_id, state])
        print table(header=['Dataset', 'Connection', 'State Model'], rows=rows)
               

##################
##################
##################
class Group_Of_Labels(persistent.Persistent):
    """
    This holds a group of labe
    """
    def __init__(self):
        self.labels = BTrees.IOBTree.BTree()

    def get_labels(self):
        return self.labels.values()

    def get_label(self, name):
        """" Given a name, return the label object """
        for label in self.get_labels():
            if label.get_name() == name:
                return label
        return False

    def search_connection_in_label(self, connection_id):
        """ Given a connection id, print the label """
        for label in self.get_labels():
            datasets = label.get_datasets()
            for dataset in datasets:
                if label.has_connection(dataset, connection_id):
                    print_info('Found in label: {}'.format(label.get_name()))
                    return label.get_id()

    def search_label_name(self, name, verbose = True):
        """ Given a name, return the labels that match"""
        matches = []
        rows = []
        for label in self.get_labels():
            if str(name) in label.get_name():
                matches.append(label.get_name())
                rows.append([label.get_id(), label.get_name(), label.get_datasets(), label.get_connections()])

        if matches and verbose:
            print_info('Labels matching the search criteria')
            print table(header=['Id', 'Label Name', 'Datasets', 'Connections'], rows=rows)
        return matches

    def list_labels(self):
        """ List all the labels """
        for label in self.get_labels():
            rows = []
            if __datasets__.current:
                if label.has_dataset(__datasets__.current.get_id()):
                    rows.append([label.get_id(), label.get_name(), __datasets__.current.get_id(), label.get_connections()])
                    print table(header=['Id', 'Label Name', 'Dataset', 'Connection'], rows=rows)
            else:
                for dataset in label.get_datasets():
                    rows.append([label.get_id(), label.get_name(), dataset, label.get_connections()])
                    print table(header=['Id', 'Label Name', 'Dataset', 'Connection'], rows=rows)

    def check_label_existance(self, dataset_id, connection_id):
        """ Get a dataset id and connection id and check if we already have a label for them """
        try:
            for label in self.get_labels():
                if label.has_connection(dataset_id, connection_id):
                    return label.get_id()
            return False
        except AttributeError:
            return False

    def add_label(self, connection_id):
        """ Add a label """
        if __datasets__.current:
            dataset_id = __datasets__.current.get_id()
            has_label = self.check_label_existance(dataset_id, connection_id)
            if has_label:
                print_error('This connection from this dataset was already assigned the label id {}'.format(has_label))
            else:
                print_warning('Remember that a label should represent a unique behavioral model!')
                #print_info('This connection does not have a prior label, assigning a new one')
                try:
                    label_id = self.labels[list(self.labels.keys())[-1]].get_id() + 1
                except (KeyError, IndexError):
                    label_id = 1
                name = self.decide_a_label_name(dataset_id, connection_id)
                if name:
                    previous_label = self.search_label_name(name, verbose=False)
                    if previous_label:
                        label = self.get_label(name)
                        label.add_connection(dataset_id, connection_id)
                    else:
                        label = Label(label_id)
                        label.set_name(name)
                        label.add_connection(dataset_id, connection_id)
                        self.labels[label_id] = label
                    # Add the auto label to the connection
                    #note.add_auto_text_to_note(note_id, text_to_add)
                else:
                    print_error('Aborting the assignment of the label.')
                    return False
        else:
            print_error('There is no dataset selected.')

    def del_label(self, lab_id):
        """ Delete a label """
        try:
            label_id = int(lab_id)
            label = self.labels[label_id]
            self.labels.pop(label_id)
        except KeyError:
            print_error('Label id does not exists.')

    def show_models_in_label(self,label_id):
        """ Show the behavioral models for all the connections in the label"""
        label = self.get_label(label_id)
        if label:
            label.show_models()

    def decide_a_label_name(self, dataset_id, connection_id):
        # Direction
        print ("Please provide a direction. It means 'From' or 'To' the most important IP in the connection: ")
        text = raw_input().strip()
        if 'From' in text or 'To' in text:
            direction = text
        else:
            print_error('Only those options are available. If you need more, please submit a request')
            return False
        # Main decision
        print ("Please provide the main decision. 'Botnet', 'Normal', 'Attack', or 'Background': ")
        text = raw_input().strip()
        if 'Botnet' in text or 'Normal' in text or 'Attack' in text or 'Background' in text:
            decision = text
        else:
            print_error('Only those options are available. If you need more, please submit a request')
            return False
        # Main 3 layer proto
        #print ("Please provide the main proto up to layer 3. 'TCP', 'UDP', 'ICMP', 'IGMP', 'ARP': ")
        #text = raw_input().strip()
        if 'TCP' in connection_id.upper():
            proto3 = 'TCP'
        elif 'UDP' in connection_id.upper():
            proto3 = 'UDP'
        elif 'ICMP' in connection_id.upper():
            proto3 = 'ICMP'
        elif 'IGMP' in connection_id.upper():
            proto3 = 'IGMP'
        elif 'ARP' in connection_id.upper():
            proto3 = 'ARP'
        else:
            print_error('The protocol of the connection could not be detected.')
            return False
        # Main 4 layer proto
        print ("Please provide the main proto in layer 4. 'HTTP', 'HTTPS', 'FTP', 'SSH', 'DNS', 'SMTP', 'P2P', 'Unknown' or 'None': ")
        text = raw_input().strip()
        if 'HTTP' in text or 'HTTPS' in text or 'FTP' in text or 'SSH' in text or 'DNS' in text or 'SMTP' in text or 'P2P' in text or 'Unknown' in text or 'None' in text:
            proto4 = text
        else:
            print_error('Only those options are available. If you need more, please submit a request')
            return False
        # Details
        print ("Please provide optional details for this connection. Up to 20 chars (No - or spaces allowed). Example: 'Encrypted', 'PlainText', 'CustomEncryption', 'soundcound.com', 'microsoft.com', 'netbios': ")
        text = raw_input().strip()
        if len(text) <= 20 and '-' not in text and ' ' not in text:
            details = text
        else:
            print_error('Only those options are available. If you need more, please submit a request')
            return False

        name_so_far = direction+'-'+decision+'-'+proto3+'-'+proto4+'-'+details

        # Separator id
        # Search for labels with this 'name' so far
        matches = self.search_label_name(name_so_far, verbose=True)
        if matches:
            print_info("There are other labels with the same name. You can input 'NEW' to create a new label with this name and a new id, or you can input the id numer to add this connection to that label. Any other input will stop the creation of the label to let you inspect the content of the labels.")
            text = raw_input().strip()
            # Is it an int?
            try:
                inttext = int(text)
                # Do we have that id?
                for match in matches:
                    # If the id of this match is the inputed id
                    if int(match.split('-')[-1]) == inttext:
                        id = match.split('-')[-1]
                        name = name_so_far + '-' + id
                        return name
                print_error('No previous label with that id.')
                return False
            except ValueError:
                # Is text
                if text == 'NEW':
                    last_id = int(matches[-1].split('-')[-1])
                    new_id = str(last_id + 1)
                    name = name_so_far + '-' + new_id
                else:
                    return False
        else:
            name = name_so_far + '-1'
        return name

    def delete_connection(self, dataset_id, connection_id):
        """ Get a dataset_id, connection id, find and delete it from the label """
        for label in self.get_labels():
            if label.has_connection(dataset_id, connection_id):
                label.delete_connection(dataset_id, connection_id)
                # We should return because is unique the key... there won't be any more
                return True


__group_of_labels__ = Group_Of_Labels()
