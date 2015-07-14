# This file was partially taken from Viper 
# See the file 'LICENSE' for copying permission.

import persistent
import BTrees.IOBTree
import os
import sys
import re

from stf.common.out import *
from stf.core.dataset import __datasets__
from stf.core.models import __groupofgroupofmodels__
from stf.core.connections import __group_of_group_of_connections__
from stf.core.notes import   __notes__


########################
########################
########################
class Label(persistent.Persistent):
    """ A class to manage a single label"""
    def __init__(self,id):
        self.id = id
        self.name = ''
        # This holds all the connections IDs in the label
        self.connections = {}

    def get_id(self):
        return self.id

    def set_id(self, i):
        self.id = id

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def change_dataset_id_to_group_of_models_id(self, dataset_id, group_of_models_id):
        """ Exactly what the name says"""
        prev_values = self.connections[dataset_id]
        self.connections.pop(dataset_id)
        self.connections[group_of_models_id] = prev_values
        self._p_changed = 1

    def get_groups_id(self):
        """ Return the ids of the groups of connections related to this label """
        return self.connections.keys()

    def add_connection(self, group_of_model_id, connection_id):
        """ Receive a group_of_model_id and a connection_id and store them in this label"""
        try:
            d_id = self.connections[group_of_model_id]
            self.connections[group_of_model_id].append(connection_id)
            self._p_changed = 1
        except KeyError:
            # First time we see this dataset id
            self.connections[group_of_model_id] = []
            self.connections[group_of_model_id].append(connection_id)
            self._p_changed = 1
        
    def delete_connection(self, group_of_model_id, connection_id):
        """ Delete this connection in this label """
        try:
            for conn in self.connections[group_of_model_id]:
                if conn == connection_id:
                    # Before removing the connection from the label we should remove the label from its model

                    self.connections[group_of_model_id].remove(connection_id)
                    # For some strange reason this is needed when we change a label
                    self._p_changed = 1
                    return True
            # We have the group_of_model_id but not the connection_id
            return False
        except KeyError:
            # We dont have that group_of_model_id
            return False

    def has_connection(self, group_of_model_id, connection_id):
        """ Check if we have this connection in this label """
        try:
            for conn in self.connections[group_of_model_id]:
                if conn == connection_id:
                    return True
            # We have the group_of_model_id but not the connection_id
            return False
        except KeyError:
            # We dont have that group_of_model_id
            return False

    def has_dataset(self, dataset_id):
        """ Check if this label has any connection with this group_of_model_id"""
        # Check if some of our connections come from this dataset id
        for group_of_model_id in self.connections:
            if group_of_model_id.split('-')[0] == str(dataset_id):
                return True
        return False

    def get_group_of_model_id(self, datasetid=False):
        ids = []
        for id in self.connections:
            if datasetid:
                if id.split('-')[0] == str(datasetid):
                    ids.append(id)
            else:
                ids.append(id)
        return ids

    def get_connections_complete(self):
        """ Return the connections object complete, with dataset id also"""
        return self.connections

    def get_connections(self, groupofmodelid=False, dataset_id=False):
        conns = []
        for id in self.connections:
            temp_dataset_id = id.split('-')[0]
            if dataset_id:
                if temp_dataset_id == str(dataset_id):
                    conns.append(self.connections[id])
            elif groupofmodelid:
                if id == groupofmodelid:
                    conns.append(self.connections[id])
            else:
                conns.append(self.connections[id])
        return conns[0]



##################
##################
##################
class Group_Of_Labels(persistent.Persistent):
    """
    This holds a group of labe
    """
    def __init__(self):
        self.labels = BTrees.IOBTree.BTree()

    def get_labels_ids(self):
        """ Return the ids of the labels"""
        return self.labels.keys()

    def get_labels(self):
        return self.labels.values()

    def get_label_by_id(self, label_id):
        """ Return the label object by its id"""
        try:
            return self.labels[label_id]
        except TypeError:
            print_error('The label id should be integer.')
            return False
        except KeyError:
            # The label was probably deleted.
            return False

    def get_label_name_by_id(self, label_id):
        """ Get the name of the label by its id"""
        label = self.get_label_by_id(label_id)
        return label.get_name()

    def get_label(self, name):
        """" Given a name, return the label object """
        for label in self.get_labels():
            if label.get_name() == name:
                return label
        return False

    def search_connection_in_label(self, connection_id):
        """ Given a connection id, print the label """
        for label in self.get_labels():
            datasets = label.get_group_of_model_id()
            for dataset in datasets:
                if label.has_connection(dataset, connection_id):
                    print_info('Found in label: {}'.format(label.get_name()))
                    return label.get_id()

    def search_label_name(self, name, verbose = True, exact = 1):
        """ Given a name, return the labels that match. exact=1 means exact mathching of the name without the final number, and exact=3 means any substring of the name without the final number. """
        matches = []
        rows = []
        for label in self.get_labels():
            # Take the name of the label except the last id
            temp_name = '-'.join(label.get_name().split('-')[0:-1])
            # Exact 2 is a complete match with the given string. Original label has the id truncated
            if exact == 1:
                if str(name) == temp_name:
                    matches.append(label.get_name())
                    rows.append([label.get_id(), label.get_name(), label.get_group_of_model_id(), label.get_connections()])
            # Exact 2 is a complete match with the given string. Original label has the id truncaed
            elif exact == 2:
                # Exact without the last id
                lastpart = name.split('-')[-1]
                try:
                    lastpart = int(lastpart)
                    # New name without the last int
                    shortname = '-'.join(name.split('-')[0:-1])
                    if str(shortname) == temp_name:
                        matches.append(label.get_name())
                        rows.append([label.get_id(), label.get_name(), label.get_group_of_model_id(), label.get_connections()])
                except ValueError:
                    matches.append(False)
            # Exact 3 is any partial match with the given string. Original label has the id truncaed
            elif exact == 3:
                if str(name).lower() in temp_name.lower():
                    matches.append(label.get_name())
                    rows.append([label.get_id(), label.get_name(), label.get_group_of_model_id(), label.get_connections()])

        if matches and verbose:
            print_info('Labels matching the search criteria')
            print table(header=['Id', 'Label Name', 'Group of Models', 'Connections'], rows=rows)
        return matches

    def construct_filter(self, filter):
        """ Get the filter string and decode all the operations """
        # If the filter string is empty, delete the filter variable
        if not filter:
            try:
                del self.filter 
            except:
                pass
            return True
        self.filter = []
        for part in filter:
            # Get the key
            try:
                key = re.split('\!=|>=|<=|=|<|>', part)[0]
                value = re.split('\!=|>=|<=|=|<|>', part)[1]
            except IndexError:
                # No < or > or = or != in the string. Just stop.
                break
            # We should search for <= before <
            try:
                part.index('<=')
                operator = '<='
                self.filter.append((key, operator, value))
                continue
            except ValueError:
                # Now we search for <
                try:
                    part.index('<')
                    operator = '<'
                    self.filter.append((key, operator, value))
                    continue
                except ValueError:
                    pass
            # We should search for >= before >
            try:
                part.index('>=')
                operator = '>='
                self.filter.append((key, operator, value))
                continue
            except ValueError:
                # Now we search for >
                try:
                    part.index('>')
                    operator = '>'
                    self.filter.append((key, operator, value))
                    continue
                except ValueError:
                    pass
            # We should search for != before =
            try:
                part.index('!=')
                operator = '!='
                self.filter.append((key, operator, value))
                continue
            except ValueError:
                # Now we search for =
                try:
                    part.index('=')
                    operator = '='
                    self.filter.append((key, operator, value))
                    continue
                except ValueError:
                    pass

    def apply_filter(self, model):
        """ Use the stored filter to know what we should match"""
        responses = []
        try:
            self.filter
        except AttributeError:
            # If we don't have any filter string, just return true and show everything
            return True
        # Check each filter
        for filter in self.filter:
            key = filter[0]
            operator = filter[1]
            value = filter[2]
            if key == 'name':
                labelname = model.get_name()
                if operator == '=':
                    if value in labelname:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '!=':
                    if value not in labelname:
                        responses.append(True)
                    else:
                        responses.append(False)
            elif key == 'groupid':
                groupsid = model.get_groups_id()
                if operator == '=':
                    for gid in groupsid:
                        if value in gid:
                            responses.append(True)
                        else:
                            responses.append(False)
                elif operator == '!=':
                    for gid in groupsid:
                        if value not in gid:
                            responses.append(True)
                        else:
                            responses.append(False)
            elif key == 'id':
                id = float(model.get_id())
                value = float(value)
                if operator == '=':
                    if id == value:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '!=':
                    if id != value:
                        responses.append(True)
                    else:
                        responses.append(False)
            elif key == 'connid':
                conn_vect = model.get_connections()
                for connid in conn_vect:
                    if operator == '=':
                        if value in connid:
                            responses.append(True)
                        else:
                            responses.append(False)
                    elif operator == '!=':
                        if value not in connid:
                            responses.append(True)
                        else:
                            responses.append(False)
            else:
                return False

        for response in responses:
            if not response:
                return False
        return True

    def list_labels(self, filter):
        """ List all the labels """
        self.construct_filter(filter)
        rows = []
        for label in self.get_labels():
            if self.apply_filter(label):
                for group_of_model_id in label.get_group_of_model_id():
                    rows.append([label.get_id(), label.get_name(), group_of_model_id, label.get_connections(groupofmodelid=group_of_model_id)])
        print table(header=['Id', 'Label Name', 'Group of Model', 'Connection'], rows=rows)

    def check_label_existance(self, group_of_model_id, connection_id):
        """ Get a dataset id and connection id and check if we already have a label for them """
        try:
            for label in self.get_labels():
                if label.has_connection(group_of_model_id, connection_id):
                    return label.get_id()
            return False
        except AttributeError:
            return False

    def add_label_with_filter(self, group_of_model_id, filter):
        """ Add a label using the filters to a group of connection ids"""
        if __datasets__.current:
            dataset_id_standing = __datasets__.current.get_id()
            dataset_id = group_of_model_id.split('-')[0]
            if str(dataset_id_standing) != dataset_id:
                print_error('You should select the dataset you are going to work in. Not another')
                return False
            if not __groupofgroupofmodels__.get_group(group_of_model_id):
                print_error('That group of models does not exist.')
                return False
            print_warning('Remember that a label should represent a unique behavioral model!')
            # Get the base name of the labels
            temp_general_name = self.decide_a_label_name("") # Connection id is empty because we are not checking the protos. This is used because we need to assign a label to multiple connections id.
            if temp_general_name:
                # The general name of the label is the one every connection will share except the final number that will change.
                # The general_name_id is the final number that will keep changing
                general_name = '-'.join(temp_general_name.split('-')[0:-1])
                general_name_id = int(temp_general_name.split('-')[-1])
                # Get all the connections from the connection model
                group_of_connections_id = int(group_of_model_id.split('-')[0])
                group_of_connections = __group_of_group_of_connections__.get_group(group_of_connections_id)
                connections = group_of_connections.get_connections()
                # Construct the filter
                self.construct_filter(filter)
                # Check we are using the correct filters
                for temp_filter in self.filter:
                    if temp_filter[0] != "connid" :
                        print_error('Adding labels with a filter only supports the type of filter connid= and connid!=')
                        return False
                    elif temp_filter[1] != "=" and temp_filter[1] != "!=":
                        print_error('Adding labels with a filter only supports the type of filter connid= and connid!=')
                        return False

                for connection in connections:
                    connection_id = connection.get_id()
                    if self.apply_filter(label):
                        has_label = self.check_label_existance(group_of_model_id, connection_id)
                        if has_label:
                            print_error('This connection from this dataset was already assigned the label id {}. We did not change it.'.format(has_label))
                            continue
                        # Get next label id
                        try:
                            label_id = self.labels[list(self.labels.keys())[-1]].get_id() + 1
                        except (KeyError, IndexError):
                            label_id = 1
                        # Obtain the name
                        name = general_name + '-' + str(general_name_id)
                        label = Label(label_id)
                        label.set_name(name)
                        #print_info('Assigning label to connection: {}'.format(connection_id))
                        label.add_connection(group_of_model_id, connection_id)
                        # Add label id to the model
                        self.add_label_to_model(group_of_model_id, connection_id, name)
                        # add auto note with the label to the model
                        self.add_auto_label_for_connection(group_of_model_id, connection_id, name)
                        self.labels[label_id] = label
                        general_name_id += 1
            else:
                # This is not necesary, but is a precaution
                print_error('Aborting the assignment of the label.')
                return False
        else:
            print_error('There is no dataset selected.')


    def add_label(self, group_of_model_id, connection_id):
        """ Add a label """
        if __datasets__.current:
            dataset_id_standing = __datasets__.current.get_id()
            dataset_id = group_of_model_id.split('-')[0]
            if str(dataset_id_standing) != dataset_id:
                print_error('You should select the dataset you are going to work in. Not another')
                return False
            if not __groupofgroupofmodels__.get_group(group_of_model_id):
                print_error('That group of models does not exist.')
                return False
            has_label = self.check_label_existance(group_of_model_id, connection_id)
            if has_label:
                print_error('This connection from this dataset was already assigned the label id {}'.format(has_label))
            else:
                print_warning('Remember that a label should represent a unique behavioral model!')
                try:
                    label_id = self.labels[list(self.labels.keys())[-1]].get_id() + 1
                except (KeyError, IndexError):
                    label_id = 1
                name = self.decide_a_label_name(connection_id)
                if name:
                    previous_label = self.search_label_name(name, verbose=False, exact=1)
                    if previous_label:
                        label = self.get_label(name)
                        label.add_connection(group_of_model_id, connection_id)
                    else:
                        label = Label(label_id)
                        label.set_name(name)
                        label.add_connection(group_of_model_id, connection_id)
                        self.labels[label_id] = label
                    # Add label id to the model
                    self.add_label_to_model(group_of_model_id, connection_id, name)
                    # add auto note with the label to the model
                    self.add_auto_label_for_connection(group_of_model_id, connection_id, name)
                else:
                    # This is not necesary, but is a precaution
                    print_error('Aborting the assignment of the label.')
                    return False
        else:
            print_error('There is no dataset selected.')

    def get_the_model_of_a_connection(self, group_of_model_id, connection_id):
        """ Given a connection_id and group of model id, get the model """
        # Get the note id, group_id and group
        dataset_id = int(group_of_model_id.split('-')[0])
        dataset = __datasets__.get_dataset(dataset_id)
        group = __groupofgroupofmodels__.get_group(group_of_model_id)
        try:
            if group.has_model(connection_id):
                model = group.get_model(connection_id)
                return model
        except AttributeError:
            print_error('The connection does not have a model. Probably deleted.')
            return False

    def add_label_to_model(self, group_of_model_id, connection_id, name):
        """ Given a connection id, label id and a current dataset, add the label id to the model"""
        model = self.get_the_model_of_a_connection(group_of_model_id, connection_id)
        try:
            model.set_label_name(name)
        except AttributeError:
            print_error('Non existant label')
            return False

    def del_label_in_model(self, group_of_model_id, connection_id, name):
        """ Given a connection id, label id and a current dataset, del the label id in the model"""
        model = self.get_the_model_of_a_connection(group_of_model_id, connection_id)
        try:
            model.del_label_name(name)
        except AttributeError:
            print_error('Non existant label')
            return False

    def add_auto_label_for_connection(self, group_of_model_id, connection_id, name):
        """ Given a connection id, label name and a current dataset, add an auto note"""
        text_to_add = "Added label {}".format(name)
        model = self.get_the_model_of_a_connection( group_of_model_id, connection_id)
        try:
            note_id = model.get_note_id()
        except AttributeError:
            print_error('Some error trying to read tht note id of the model.')
            return False
        if not note_id:
            # There was not originaly a note, so we should now store the new created not in the model.
            note_id =__notes__.new_note()
            model.set_note_id(note_id)
        __notes__.add_auto_text_to_note(note_id, text_to_add)
        print_info('Connection has note id {}'.format(note_id))

    def del_label(self, lab_id):
        """ Delete a label """
        try:
            if '-' in lab_id:
                # Probable range
                try:
                    first_id = int(lab_id.split('-')[0])
                    second_id = int(lab_id.split('-')[1])
                except ValueError:
                    print_error('Invalid label id')
                    return False
            else:
                try:
                    first_id = int(lab_id)
                    second_id = int(lab_id)
                except ValueError:
                    print_error('Invalid label id')
                    return False
            for id in range(first_id, second_id + 1):
                label = self.labels[int(id)]
                # First delete the label from the model
                for group_id in label.get_group_of_model_id():
                    for conn_id in label.get_connections(groupofmodelid=group_id):
                        self.del_label_in_model(group_id, conn_id, label.get_name())
                # Now delete the label itself
                self.labels.pop(id)
        except KeyError:
            print_error('Label id does not exists. Delete only continuous ranges.')

    def protocols_match(self, old_connection, new_connection):
        """ Check that the protocols in both connection id match """
        current_proto = str(old_connection.split('-')[-1])
        new_proto = str(new_connection.split('-')[-1])
        if current_proto == new_proto:
            return True
        else:
            return False

    def decide_a_label_name(self, connection_id):
        """ Get a connection id and return a label for it. The connection_id can be empty"""
        # First choose amount the current labels
        print_info('Current Labels')
        # List all the labels, i.e. with an empty filter
        self.list_labels("")
        selection = raw_input('Select a label Id to assign the same label BUT with a new final number to the current connection. Or press Enter to create a new one:')
        try:
            # Get the label selected with an id
            label = self.get_label_by_id(int(selection))
            # Get its name
            name = label.get_name()
            # Now get all the labels named the same (except the last number)
            matches = self.search_label_name(name, verbose=False, exact=2)
            last_name = matches[-1]
            last_id = int(last_name.split('-')[-1])
            last_name_without_id = '-'.join(last_name.split('-')[0:-1])
            new_id = last_id + 1
            new_name = last_name_without_id + '-' + str(new_id)
            # Check that the protocols match
            first_connection = label.get_connections()[0]
            # If we have a connection_id, check that the protocol is ok. (The connection_id can be empty when assigning to multiple connections)
            if connection_id != "" and self.protocols_match(first_connection, connection_id):
                return new_name
            elif connection_id != "":
                print_error('Protocols in both connection ids should match. ({} and {})'.format(first_connection, connection_id))
                return False
            else:
                return new_name
        except ValueError:
            pass

        # Direction
        print ("Please provide a direction. It means 'From' or 'To' the most important IP in the connection: ")
        text = raw_input().strip()
        if 'From' in text or 'To' in text:
            direction = text
        else:
            print_error('Only those options are available. If you need more, please submit a request')
            return False
        # Main decision
        print ("Please provide the main decision. 'Botnet', 'Malware', 'Normal', 'Attack', or 'Background': ")
        text = raw_input().strip()
        if 'Botnet' in text or 'Malware' in text or 'Normal' in text or 'Attack' in text or 'Background' in text:
            decision = text
        else:
            print_error('Only those options are available. If you need more, please submit a request')
            return False
        # Main 3 layer proto
        print ("Please provide the layer 3 proto. 'TCP', 'UDP', 'ICMP', 'IGMP', or 'ARP': ")
        text = raw_input().strip()
        if 'TCP' in text or 'UDP' in text or 'ICMP' in text or 'IGMP' in text or 'ARP' in text:
            proto3 = text
        else:
            print_error('Only those options are available. If you need more, please submit a request')
            return False
        # Main 4 layer proto
        print ("Please provide the main proto in layer 4. 'HTTP', 'HTTPS', 'FTP', 'SSH', 'DNS', 'SMTP', 'P2P', 'NTP', 'Multicast', 'NetBIOS', 'Unknown', 'Other', 'Custom', or 'None': ")
        text = raw_input().strip()
        if 'HTTP' in text or 'HTTPS' in text or 'FTP' in text or 'SSH' in text or 'DNS' in text or 'SMTP' in text or 'P2P' in text or 'NTP' in text or 'Multicast' in text or 'NetBIOS' in text or 'Unknown' in text or 'Other' in text or 'Custom' in text or 'None' in text:
            proto4 = text
        else:
            print_error('Only those options are available. If you need more, please submit a request')
            return False
        # Details
        print ("Please provide optional details for this connection. Up to 30 chars (No - or spaces allowed). Example: 'Encrypted', 'PlainText', 'CustomEncryption', 'soundcound.com', 'microsoft.com', 'netbios': ")
        text = raw_input().strip()
        if len(text) <= 30 and '-' not in text and ' ' not in text:
            details = text
        else:
            print_error('Only those options are available. If you need more, please submit a request')
            return False

        name_so_far = direction+'-'+decision+'-'+proto3+'-'+proto4+'-'+details

        # Separator id
        # Search for labels with this 'name' so far
        matches = self.search_label_name(name_so_far, verbose=True, exact = 3)
        if matches:
            print_info("There are other labels with a similar name. You can enter 'NEW' to create a new label with this name and a new id. Or you can input the label ID to add this connection to that label. Any other input will stop the creation of the label to let you inspect the content of the labels.")
            text = raw_input().strip()
            # Is it an int?
            try:
                inttext = int(text)
                label = self.get_label_by_id(inttext)
                if label:
                    return label.get_name()
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

    def delete_connection(self, group_of_model_id, connection_id):
        """ Get a group_of_model_id, connection id, find and delete it from the label """
        for label in self.get_labels():
            if label.has_connection(group_of_model_id, connection_id):
                ################??????
                # Delete the label from the model
                self.del_label_in_model(group_of_model_id, connection_id, label.get_name())
                # Delete the connection
                label.delete_connection(group_of_model_id, connection_id)
                # If the label does not have any more connections, we should also delete the label
                if len(label.get_connections()) == 0:
                    self.labels.pop(label.get_id())
                print_info('Connection {} in group of models id {} deleted.'.format(connection_id, group_of_model_id))
                return True

    def migrate_old_labels(self):
        """ Because of an issue in the label database of version < 0.1.2alpha, we need to migrate the labels
        The issue is that the old labels used the dataset_id as part of the id, and now we use the group_of_models_id. 
        So this migration changes the dataset_id in the db for the group_of_models_id
        """
        for label_id in self.get_labels_ids():
            label = self.get_label_by_id(label_id)
            name = label.get_name()
            for dataset_id in label.get_group_of_model_id():
                if '-' not in str(dataset_id): 
                    print_info('The label {} with id {}, has a dataset id {}. It needs to be migrated'.format(name, label_id, dataset_id))
                    # If we are migrating we expect that there is still only one type of models. so 1
                    group_of_model_id = str(dataset_id) + '-1' 
                    label.change_dataset_id_to_group_of_models_id(dataset_id, group_of_model_id)
                    print_info('\tMigrated')

    def delete_all_labels_from_dataset(self, dataset_id):
        """ Given a dataset id, delete all the connections from that dataset from the labels """
        pass


__group_of_labels__ = Group_Of_Labels()
