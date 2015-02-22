# This file was partially taken from Viper 
# See the file 'LICENSE' for copying permission.

import time
import datetime
import persistent
import BTrees.OOBTree
import transaction
import os
import re

from stf.common.out import *
from stf.core.dataset import __datasets__


class Flow(object):
    """ A class to manage a single flow"""
    def __init__(self,id):
        self.id = id
        self.line_separator = ','

    def set_t1(self,t1):
        self.t1 = t1

    def set_t2(self,t2):
        self.t2 = t2

    def set_td(self,td):
        self.td = td

    def set_state(self,state):
        self.state = state

    def get_id(self):
        return self.id

    def add_starttime(self, starttime):
        self.starttime = starttime

    def add_duration(self,dur):
        self.duratin = dur

    def add_proto(self,proto):
        self.proto = proto

    def add_scraddr(self, srcaddr):
        self.srcaddr = srcaddr

    def add_dir(self, dir):
        self.dir = dir

    def add_dstaddr(self, dstaddr):
        self.dstaddr = dstaddr

    def add_dport(self, dport):
        self.dport = dport

    def add_state(self,state):
        self.state = state

    def add_stos(self, stos):
        self.stos = stos

    def add_dtos(self, dtos):
        self.dtos = dtos

    def add_totpkts(self, totpkts):
        self.totpkts = totpkts

    def add_totbytes(self, totbytes):
        self.totbytes = totbytes

    def add_srcbytes(self, srcbytes):
        self.srcbytes = srcbytes

    def add_label(self,label):
        self.label = label

    def get_starttime(self):
        return self.starttime 

    def get_duration(self):
        return self.duratin 

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

    def get_state(self):
        return self.state 

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

    def get_label(self):
        return self.label

    def get_field_separator(self):
        return self.line_separator

    def __repr__(self):
        return (self.get_field_separator().join([str(self.get_id()),self.get_starttime(),self.get_duration(),self.get_proto(),self.get_scraddr(),self.get_dir(),self.get_dstaddr(),self.get_dport(),self.get_state(),self.get_stos(),self.get_dtos(),self.get_totpkts(),self.get_totbytes(),self.get_srcbytes(),self.get_label()]))




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
        StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,Label
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
        column_values = {}
        i = 0
        temp_values = line.split(self.line_separator)
        for value in temp_values:
            column_values[self.columns_names[i]] = value
            i += 1
        return column_values

    def get_connections(self):
        """ Returns the list of connections """
        return self.connections.values()

    def get_connection(self, column_values):
        """ Finds the connection for this data or creates a new one"""
        tuple4 = column_values['SrcAddr']+'-'+column_values['DstAddr']+'-'+column_values['Dport']+'-'+column_values['Proto']
        try:
            connection = self.connections[tuple4]
            # We already have this connection
        except KeyError:
            # First time for this connection
            connection = Connection(tuple4)
            self.connections[tuple4] = connection
        return connection

    def del_connection(self,id):
        """ Delete a specific connection inside the group"""
        try:
            self.connections.pop(id)
        except KeyError:
            print_error('There is no such connection id.')


    def create_connections(self):
        """ Read the flows and creates the connections """
        # Don't create the connections if we already have them

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
                if filter_key == 'nameincludes':
                    name = connection.get_id()
                    if operator == '=':
                        if value in name:
                            return True
            return False
        except AttributeError:
            # If we don't have any filter string, just return true and show everything
            return True

    def list_connections(self, filter_string=''):
        rows = []
        # set the filter
        self.construct_filter(filter_string)
        amount = 0
        print('| Connection Id ')
        for connection in self.connections.values():
            if self.apply_filter(connection):
                print_row([connection.get_id()])
                amount += 1
        print_info('Amount of connections printed: {}'.format(amount))



class Group_Of_Group_Of_Connections(persistent.Persistent):
    """ A class to manage all the connections for all the datasets. Each dataset may have one group of connections. """
    def __init__(self):
        # The index of the group_of_connections is the dataset id
        self.group_of_connections = BTrees.OOBTree.BTree()

    def get_group(self,id):
        try:
            return self.group_of_connections[id]
        except KeyError:
            return False

    def create_group_of_connections(self,binetflow_filename, dataset_id, file_id):
        """ Create a group of connections for the current dataset """

        # Don't create the connections if we already have them
        try:
            self.group_of_connections[dataset_id]
            # Is here
            print_info('This dataset already have connections')
            return False
        except KeyError:
            # First time
            new_group_of_connections = Group_Of_Connections(dataset_id)
            # The id of the group of connections is the same as the dataset because it is a 1-1 relationship
            new_group_of_connections.set_filename(binetflow_filename)
            new_group_of_connections.set_dataset_id(dataset_id)
            new_group_of_connections.set_file_id(file_id)
            self.group_of_connections[dataset_id] = new_group_of_connections
            # Order to create the connections
            new_group_of_connections.create_connections()

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

    def del_group_of_connections(self, conn_id):
        try:
            self.group_of_connections.pop(conn_id)
            print_info('Deleted group of connections with id {}'.format(conn_id))
        except KeyError:
            print_error('No such group of connections exists.')

    def list_connections_in_group(self, id, filter=''):
        try:
            group = self.group_of_connections[id]
            group.list_connections(filter)
        except KeyError:
            print_error('No such group of connections.')


__group_of_group_of_connections__ = Group_Of_Group_Of_Connections()
