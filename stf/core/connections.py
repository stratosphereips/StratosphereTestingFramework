# This file was partially taken from Viper 
# See the file 'LICENSE' for copying permission.

import time
import datetime
import persistent
import BTrees.IOBTree
import BTrees.OOBTree
import transaction
import os
import re
import sys
from subprocess import Popen
from subprocess import PIPE
import tempfile

from stf.common.out import *
from stf.core.dataset import __datasets__


########################
########################
########################
class Flow(object):
    """ A class to manage a single flow"""
    def __init__(self,id):
        self.id = id
        self.set_t1(False)
        self.set_t2(False)
        self.set_td(False)
        self.line_separator = ','

    def set_t1(self,t1):
        # T1 is usually a timedelta. but it can be also False
        self.t1 = t1

    def set_t2(self,t2):
        # T2 is usually a timedelta. but it can be also False
        self.t2 = t2


    def set_td(self,td):
        self.td = float(td)

    def set_state(self,state):
        self.state = str(state)

    def get_t1(self):
        return self.t1

    def get_t2(self):
        return self.t2

    def get_td(self):
        return self.td

    def get_state(self):
        try:
            return self.state
        except AttributeError:
            # It can be that a flow does not have a state because we generate the models, then delete the flow, and then generate the flows again.
            return ''

    def get_id(self):
        return self.id

    def add_starttime(self, starttime):
        self.starttime = starttime

    def add_duration(self,dur):
        self.duration = float(dur)

    def add_proto(self,proto):
        self.proto = str(proto)

    def add_scraddr(self, srcaddr):
        self.srcaddr = str(srcaddr)

    def add_dir(self, dir):
        self.dir = str(dir)

    def add_dstaddr(self, dstaddr):
        self.dstaddr = str(dstaddr)

    def add_dport(self, dport):
        self.dport = str(dport)

    def add_state(self,flowstate):
        self.flowstate = str(flowstate)

    def add_stos(self, stos):
        self.stos = str(stos)

    def add_dtos(self, dtos):
        self.dtos = str(dtos)

    def add_totpkts(self, totpkts):
        self.totpkts = int(totpkts)

    def add_totbytes(self, totbytes):
        self.totbytes = int(totbytes)

    def add_srcbytes(self, srcbytes):
        self.srcbytes = int(srcbytes)

    def add_srcUdata(self, srcUdata):
        self.srcUdata = str(srcUdata)

    def add_dstUdata(self, dstUdata):
        self.dstUdata = str(dstUdata)

    def add_label(self,label):
        self.label = str(label)

    def get_starttime(self):
        return self.starttime 

    def get_duration(self):
        return self.duration 

    def get_proto(self):
        return self.proto 

    def get_scraddr(self):
        return self.srcaddr

    def get_dir(self):
        return self.dir 

    def get_dstaddr(self):
        return self.dstaddr

    def get_dport(self):
        return self.dport

    def get_flowstate(self):
        return self.flowstate 

    def get_stos(self):
        return self.stos 

    def get_dtos(self):
        return self.dtos 

    def get_totpkts(self):
        return self.totpkts 

    def get_totbytes(self):
        return self.totbytes

    def get_srcbytes(self):
        return self.srcbytes 

    def get_srcUdata(self):
        try:
            return self.srcUdata
        except AttributeError:
            return ''

    def get_dstUdata(self):
        try:
            return self.dstUdata
        except AttributeError:
            return ''

    def get_label(self):
        try:
            return self.label
        except AttributeError:
            return ''

    def get_field_separator(self):
        return self.line_separator

    def __repr__(self):
        return (self.get_field_separator().join([str(self.get_id()),self.get_starttime(),self.get_duration(),self.get_proto(),self.get_scraddr(),self.get_dir(),self.get_dstaddr(),self.get_dport(),self.get_flowstate(),self.get_stos(),self.get_dtos(),self.get_totpkts(),self.get_totbytes(),self.get_srcbytes(),self.get_srcUdata(),self.get_dstUdata(),self.get_label()]))

    def print_flow(self):
        print_info(red(' State: \"' + self.get_state() + '\"') + cyan(' TD: ' + str(self.get_td()) + ' T2: ' + str(self.get_t2()) + ' T1: ' + str(self.get_t1())) + '\t' + self.get_field_separator().join([self.get_starttime(),cyan(str(self.get_duration())),self.get_proto(),self.get_scraddr(),self.get_dir(),self.get_dstaddr(),self.get_dport(),self.get_flowstate(),self.get_stos(),self.get_dtos(),str(self.get_totpkts()),cyan(str(self.get_totbytes())),str(self.get_srcbytes()),self.get_srcUdata(),self.get_dstUdata(),self.get_label()]))

    def return_flow_info(self):
        return (red(' State: \"' + self.get_state() + '\"') + cyan(' TD: ' + str(self.get_td()) + ' T2: ' + str(self.get_t2()) + ' T1: ' + str(self.get_t1())) + '\t' + self.get_field_separator().join([self.get_starttime(),cyan(str(self.get_duration())),self.get_proto(),self.get_scraddr(),self.get_dir(),self.get_dstaddr(),self.get_dport(),self.get_flowstate(),self.get_stos(),self.get_dtos(),str(self.get_totpkts()),cyan(str(self.get_totbytes())),str(self.get_srcbytes()),self.get_srcUdata(),self.get_dstUdata(),self.get_label()]))



########################
########################
########################
class Connection(object):
    """
    One 4-tuple is a connection. A dataset has a lot of these
    """
    def __init__(self, tuple4):
        self.id = tuple4
        self.flows = {}
        # Store the id of the new future flow just to make it faster
        self.new_future_flow_id = 0

    def add_new_flow(self, column_values):
        """ Add a new flow to the connection """
        # Create the new flow object
        new_flow = Flow(self.new_future_flow_id)

        # Add the info to the flow object
        new_flow.add_starttime(column_values['StartTime'])
        new_flow.add_duration(column_values['Dur'])
        new_flow.add_proto(column_values['Proto'])
        new_flow.add_scraddr(column_values['SrcAddr'])
        new_flow.add_dir(column_values['Dir'])
        new_flow.add_dstaddr(column_values['DstAddr'])
        new_flow.add_dport(column_values['Dport'])
        new_flow.add_state(column_values['State'])
        new_flow.add_stos(column_values['sTos'])
        new_flow.add_dtos(column_values['dTos'])
        new_flow.add_totpkts(column_values['TotPkts'])
        new_flow.add_totbytes(column_values['TotBytes'])
        try:
            new_flow.add_srcbytes(column_values['SrcBytes'])
        except KeyError:
            # It can happen that we don't have the SrcBytes column
            pass
        try:
            new_flow.add_srcUdata(column_values['srcUdata'])
        except KeyError:
            # It can happen that we don't have the srcUdata column
            pass
        try:
            new_flow.add_dstUdata(column_values['dstUdata'])
        except KeyError:
            # It can happen that we don't have the dstUdata column
            pass
        try:
            new_flow.add_label(column_values['Label'])
        except KeyError:
            # It can happen that we don't have the label column
            pass

        # Store the new flow
        self.flows[self.new_future_flow_id] = new_flow
        self.new_future_flow_id += 1

    def get_id(self):
        return self.id

    def get_flows(self):
        return self.flows.values()

    def show_flows(self):
        all_text=''
        for flow_id in self.flows:
            all_text = all_text + self.flows[flow_id].return_flow_info() + '\n'
        f = tempfile.NamedTemporaryFile()
        f.write(all_text)
        f.flush()
        p = Popen('less -R ' + f.name, shell=True, stdin=PIPE)
        p.communicate()
        sys.stdout = sys.__stdout__ 
        f.close()

    def delete_all_flows(self):
        """ Delete all the flows of the model"""
        for flow in self.flows.values():
            self.flows.pop(flow.get_id())

    def trim_flows(self, trim_amount):
        """ Trim the amount of flows in this connection to the first trim_amount """
        from itertools import islice
        self.flows =  dict(islice(self.flows.iteritems(), trim_amount))



########################
########################
########################
class Group_Of_Connections(object):
    """
    This holds a group of connections from the same dataset
    """
    def __init__(self, id):
        self.id = id 
        # The index of the connections is the id of the individual connection
        self.connections = BTrees.OOBTree.BTree()
        self.dataset_id = False
        self.file_id = False

    def get_id(self):
        return self.id

    def set_dataset_id(self,datasetid):
        self.dataset_id = datasetid

    def get_dataset_id(self):
        return self.dataset_id

    def get_filename(self):
        return self.filename

    def set_filename(self, filename):
        self.filename = filename

    def set_file_id(self,fileid):
        self.fileid = fileid

    def get_file_id(self):
        return self.fileid

    def find_columns_names(self,line):
        """ Usually the columns in a binetflow file are 
        StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,srcUdata,dstUdata,Label
        """
        self.columns_names = line.split(self.line_separator)
            
    def find_separator(self,line):
        count_commas = len(line.split(','))
        count_spaces = len(line.split(' '))
        if count_commas >= count_spaces:
            self.line_separator = ','
        elif count_spaces > count_commas:
            self.line_separator = ' '
        else:
            self.line_separator = ','

    def extract_columns_values(self, line):
        """ Given a line text of a flow, extract the values for each column """
        column_values = {}
        i = 0
        original_values = line.split(self.line_separator)
        temp_values = original_values
        if len(temp_values) > len(self.columns_names):
            # If there is only one occurrence of the separator char, then try to recover...

            # Find the index of srcudata
            srcudata_index_starts = 0
            for values in temp_values:
                if 's[' in values:
                    break
                else:
                    srcudata_index_starts += 1 

            # Find the index of dstudata
            dstudata_index_starts = 0
            for values in temp_values:
                if 'd[' in values:
                    break
                else:
                    dstudata_index_starts += 1 
           
            # Get all the src data
            srcudata_index_ends = dstudata_index_starts
            temp_srcudata = temp_values[srcudata_index_starts:srcudata_index_ends]
            srcudata = ''
            for i in temp_srcudata:
                srcudata = srcudata + i

            # Get all the dst data. The end is one before the last field. That we know is the label.
            dstudata_index_ends = len(temp_values) - 1
            temp_dstudata = temp_values[dstudata_index_starts:dstudata_index_ends]
            dstudata = ''
            for j in temp_dstudata:
                dstudata = dstudata + j

            label = temp_values[-1]
            
            end_of_good_data = srcudata_index_starts 
            # Rewrite temp_values
            temp_values = temp_values[0:end_of_good_data]
            temp_values.append(srcudata)
            temp_values.append(dstudata)
            temp_values.append(label)

        index = 0
        try:
            for value in temp_values:
                column_values[self.columns_names[index]] = value
                index += 1
        except IndexError:
            # Even with our fix, some data still has problems. Usually it means that there is no src data being sent, so we can not find the start of the data.
            print_error('There was some error reading the data inside a flow. Most surely it includes the field separator of the flows. We will keep the flow, but not its data.')
            # Just get the normal flow fields
            index = 0
            for value in temp_values:
                if index <= 13:
                    column_values[self.columns_names[index]] = value
                    index += 1
                else:
                    break
            column_values['srcUdata'] = 'Deleted because of inconsistencies'
            column_values['dstUdata'] = 'Deleted because of inconsistencies'
            column_values['Label'] = original_values[-1]
        return column_values

    def get_connections(self):
        """ Returns the list of connections """
        return self.connections.values()

    def get_connection_by_id(self, id):
        return self.connections[id]

    def get_connection(self, column_values):
        """ Finds the connection for this data or creates a new one"""
        """ Maybe I should get out of here the creation of the connection object"""
        tuple4 = column_values['SrcAddr']+'-'+column_values['DstAddr']+'-'+column_values['Dport']+'-'+column_values['Proto']
        try:
            connection = self.connections[tuple4]
            # We already have this connection
        except KeyError:
            # First time for this connection
            connection = Connection(tuple4)
            self.connections[tuple4] = connection
        return connection

    def delete_connection_by_id(self,id):
        """ Delete a specific connection inside the group using the id """
        try:
            # First call the deletion of all the flows objects
            self.get_connection_by_id(id).delete_all_flows()
            # Then delete the connection from the group
            self.connections.pop(id)
            # Here we should delete the flows.
        except KeyError:
            print_error('There is no such connection id.')

    def delete_all_connections(self):
        """ Delete all the connections in the group """
        ids_to_delete = []
        # For a strange reason we need to get first the ids and the delete them. If not one every two is missed
        for connection in self.get_connections():
            ids_to_delete.append(connection.get_id())
        # Now delete
        amount = 0
        for id in ids_to_delete:
            self.delete_connection_by_id(id)
            amount += 1
        print_info('Amount of connections deleted: {}'.format(amount))


    def create_connections(self):
        """ Read the flows and creates the connections """

        # Open the binetflow file
        file = open(self.filename)
        header_line = file.readline().strip()
        # Find the separation character
        self.find_separator(header_line)
        # Extract the columns names
        self.find_columns_names(header_line)
        # For each line
        line = file.readline().strip()
        while line:
            # Extract the column values
            column_values = self.extract_columns_values(line)
            # Find (or create) the connection object
            connection = self.get_connection(column_values)
            # Add the data to this connection
            connection.add_new_flow(column_values)
            # Read next line
            line = file.readline().strip()
        # Close the file
        file.close()
        
    def get_amount_of_connections(self):
        return len(self.connections)

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

    def apply_filter(self,connection):
        """ Use the stored filter to know what we should match"""
        try:
            self.filter
            for filter_key in self.filter:
                operator = self.filter[filter_key][0]
                value = self.filter[filter_key][1]
                if filter_key == 'name':
                    name = connection.get_id()
                    if operator == '=':
                        if value in name:
                            return True
                if filter_key == 'flowamount':
                    value = int(value)
                    amount_of_flows = len(connection.flows)
                    if operator == '=':
                        if value == amount_of_flows:
                            return True
                    elif operator == '<':
                        if amount_of_flows < value:
                            return True
                    elif operator == '>':
                        if amount_of_flows > value:
                            return True
                else:
                    return False
            return False
        except AttributeError:
            # If we don't have any filter string, just return true and show everything
            return True

    def list_connections(self, filter_string):
        all_text='| Connection Id | Amount of flows |\n'
        # construct the filter
        self.construct_filter(filter_string)
        amount = 0
        for connection in self.connections.values():
            if self.apply_filter(connection):
                all_text += '{:40} | {}\n'.format(connection.get_id(), len(connection.get_flows()))
                amount += 1
        all_text += 'Amount of connections printed: {}'.format(amount)
        f = tempfile.NamedTemporaryFile()
        f.write(all_text)
        f.flush()
        p = Popen('less -R ' + f.name, shell=True, stdin=PIPE)
        p.communicate()
        sys.stdout = sys.__stdout__ 
        f.close()

    def show_flows(self,connection_id):
        try:
            self.connections[connection_id].show_flows()
        except KeyError:
            print_error('That connection does not exist in this dataset.')

    def delete_connection_by_filter(self, filter):
        """ Delete connections from the group by filter """
        # construct the filter
        self.construct_filter(filter)
        ids_to_delete = []
        for connection in self.connections.values():
            if self.apply_filter(connection):
                ids_to_delete.append(connection.get_id())
        # We should delete the connections AFTER finding them, if not, for some reason the following model after a match is missed.
        amount = 0
        for id in ids_to_delete:
            self.delete_connection_by_id(id)
            amount += 1
        print_info('Amount of connections deleted: {}'.format(amount))


    def delete_connections_if_model_deleted(self):
        """ Delete the connections only of all the models related to that connection were deleted """
        from stf.core.models import __groupofgroupofmodels__
        amount = 0
        ids_to_delete = []
        for connection in self.connections.values():
            # Get the groups of groups of models
            groups_of_models = __groupofgroupofmodels__.get_groups()
            is_in_a_group = False
            for group in groups_of_models:
                # See if this group of models has models with the id of the connection
                if group.has_model(connection.get_id()):
                    is_in_a_group = True
                    break
            # If this connection
            if not is_in_a_group:
                ids_to_delete.append(connection.get_id())
                amount += 1
    
        # We should delete the connections AFTER finding them, if not, for some reason the following model after a match is missed.
        for id in ids_to_delete:
            self.delete_connection_by_id(id)
        print_info('Amount of connections deleted: {}'.format(amount))

    def trim_flows(self, trim_amount):
        """ For each connection in this group, tell it  to trim the amount of flows """
        for connection in self.connections.values():
            connection.trim_flows(trim_amount)

    def count_connections(self, filter):
        """ Count the connections in the group that match the filter """
        # construct the filter
        self.construct_filter(filter)
        amount = 0
        for connection in self.connections.values():
            if self.apply_filter(connection):
                amount += 1
        print_info('Amount of connections that match the filter: {}'.format(amount))


########################
########################
########################
class Group_Of_Group_Of_Connections(persistent.Persistent):
    """ A class to manage all the connections for all the datasets. Each dataset may have one group of connections. """
    def __init__(self):
        # The index of the group_of_connections is the dataset id
        self.group_of_connections = BTrees.IOBTree.BTree()

    def get_group(self,id):
        try:
            return self.group_of_connections[id]
        except KeyError:
            return False

    def create_group_of_connections(self):
        """ Create a group of connections for the current dataset """
        # We should have a current dataset
        if __datasets__.current:
            # We should have a binetflow file in the dataset
            binetflow_file = __datasets__.current.get_file_type('binetflow')
            try:
                binetflow_filename = binetflow_file.get_name()
            except:
                print_error('You should have a binetflow file in your dataset. Use datasets -g')
                return False
            file_id = binetflow_file.get_id()
            if binetflow_file:
                # Don't create the connections if we already have them
                group_of_connections_id = __datasets__.current.get_group_of_connections_id()
                if group_of_connections_id:
                    # Do we already have a group of connections for this dataset?
                    # Is here
                    print_info('This dataset already have connections')
                    return False
                else:
                    dataset_id = __datasets__.current.get_id()
                    # First time
                    # The id of the group of connections is the same as the dataset because it is a 1-1 relationship
                    group_of_connections_id = dataset_id
                    new_group_of_connections = Group_Of_Connections(group_of_connections_id)
                    new_group_of_connections.set_filename(binetflow_filename)
                    new_group_of_connections.set_dataset_id(dataset_id)
                    new_group_of_connections.set_file_id(file_id)
                    self.group_of_connections[group_of_connections_id] = new_group_of_connections
                    # Order to create the connections
                    new_group_of_connections.create_connections()
                    __datasets__.current.set_group_of_connections_id(group_of_connections_id)
            else:
                print_error('You should have a binetflow file in your dataset. Use datasets -g')
                return False
        else:
            print_error('You should first select a dataset with datasets -s <id>')
            return False

    def list_group_of_connections(self):
        """ List all the groups of connections """
        print_info("Groups of Connections Available:")
        rows = []
        if __datasets__.current :
            for group_connection in self.group_of_connections.values():
                if __datasets__.current.get_id() == group_connection.get_id():
                    rows.append([group_connection.get_id(), group_connection.get_dataset_id(), group_connection.get_filename(), group_connection.get_amount_of_connections()])
        else:
            for group_connection in self.group_of_connections.values():
                rows.append([group_connection.get_id(), group_connection.get_dataset_id(), group_connection.get_filename(), group_connection.get_amount_of_connections()])
        print(table(header=['Id of Group of Connections', 'Dataset Id', 'Filename', 'Amount of Connections'], rows=rows))

    def delete_group_of_connections(self, conn_id):
        group = self.get_group(conn_id)
        if group:
            # First delete all the connections inside the group of connections
            group.delete_all_connections()
            # Now delete the group of connections
            self.group_of_connections.pop(conn_id)
            print_info('Deleted group of connections with id {}'.format(conn_id))
            # Delete the reference to this group from the dataset
            dataset = __datasets__.get_dataset(conn_id)
            dataset.remove_group_of_connections_id(conn_id)
        else:
            print_error('No such group of connections exists.')

    def list_connections_in_group(self, id, filter):
        try:
            group = self.group_of_connections[id]
            group.list_connections(filter)
        except KeyError:
            print_error('No such group of connections.')

    def show_flows_in_connnection(self, connection_id, filter):
        """ Show the flows inside a connection """
        if __datasets__.current:
            group_id = __datasets__.current.get_id()
            try:
                self.group_of_connections[group_id].show_flows(connection_id)
            except KeyError:
                print_error('The connection {} does not longer exists in the database.'.format(connection_id))
        else:
            print_error('There is no dataset selected.')

    def delete_a_connection_from_the_group_by_id(self, group_id, connection_id):
        """ Delete a unique connection id from a connection group """
        if __datasets__.current:
            self.group_of_connections[group_id].delete_connection_by_id(connection_id)
        else:
            # This is not necesary to work, but is a nice precaution
            print_error('There is no dataset selected.')

    def delete_a_connection_from_the_group_by_filter(self, group_id, filter):
        """ Delete connections from a the group by filter """
        if __datasets__.current:
            group = self.get_group(int(group_id))
            group.delete_connection_by_filter(filter)
        else:
            # This is not necesary to work, but is a nice precaution
            print_error('There is no dataset selected.')

    def delete_a_connection_from_the_group_if_model_deleted(self, group_id):
        """ Delete connections from a connection group using the filter"""
        if __datasets__.current:
            # Get the id of the groups of connections
            group_of_connections_id = __datasets__.current.get_group_of_connections_id()
            self.group_of_connections[group_id].delete_connections_if_model_deleted()
        else:
            # This is not necesary to work, but is a nice precaution
            print_error('There is no dataset selected.')

    def trim_flows(self, group_of_connections_id, trim_amount):
        """ Get a group id and call the trimmer on the group """
        if __datasets__.current:
            group = self.get_group(group_of_connections_id)
            if group:
                group.trim_flows(trim_amount)
            else:
                print_error('No group with that id.')
        else:
            # This is not necesary to work, but is a nice precaution
            print_error('There is no dataset selected.')

    def count_connections_in_group(self, group_of_connections_id, filter):
        if __datasets__.current:
            group = self.get_group(int(group_of_connections_id))
            if group:
                group.count_connections(filter)
            else:
                print_error('No group with that id.')

        else:
            # This is not necesary to work, but is a nice precaution
            print_error('There is no dataset selected.')
        


__group_of_group_of_connections__ = Group_Of_Group_Of_Connections()
