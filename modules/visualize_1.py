# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# This is a template module showing how to create a module that has persistence in the database. To create your own command just copy this file and start modifying it.

import persistent
import BTrees.OOBTree
import curses
import multiprocessing
from multiprocessing import Queue
from multiprocessing import JoinableQueue
import time
from datetime import datetime
import re


from stf.common.out import *
from stf.common.abstracts import Module
from stf.core.dataset import __datasets__
from stf.core.models_constructors import __modelsconstructors__ 
from stf.core.database import __database__
from stf.core.connections import Flow
from stf.core.models import Model


######################
######################
######################
class Screen(multiprocessing.Process):
    """ A class thread to run the screen """
    def __init__(self, qscreen):
        multiprocessing.Process.__init__(self)
        self.qscreen = qscreen
        self.tuples = {}
        self.global_x_pos = 1
        self.y_min = 46
        self.f = open('log2','w')

    def get_tuple(self, tuple_id):
        """ Get a tuple, return its dict """
        try:
            return self.tuples[tuple_id]
        except KeyError:
            # first time for this tuple
            self.tuples[tuple_id] = {}
            self.tuples[tuple_id]['y_pos'] = self.y_min
            self.tuples[tuple_id]['x_pos'] = self.global_x_pos
            (x_max, y_max) = self.screen.getmaxyx()
            if self.global_x_pos <= x_max - 2:
                self.global_x_pos += 1
            if 'tcp' in tuple_id.lower():
                self.tuples[tuple_id]['color'] = curses.color_pair(1)
            elif 'udp' in tuple_id.lower():
                self.tuples[tuple_id]['color'] = curses.color_pair(2)
            elif 'icmp' in tuple_id.lower():
                self.tuples[tuple_id]['color'] = curses.color_pair(3)
            else:
                self.tuples[tuple_id]['color'] = curses.color_pair(4)
            # print the tuple
            self.screen.addstr(self.tuples[tuple_id]['x_pos'],0, tuple_id)
            return self.tuples[tuple_id]

    def run(self):
        try:
            while True:
                #print 'Is the queue empty?: {}'.format(self.qscreen.empty())
                if not self.qscreen.empty():
                    order = self.qscreen.get()
                    #self.logfile.write('Receiving the order'+order+'\n')
                    if order == 'Start':
                        stdscr = curses.initscr()
                        curses.savetty()
                        curses.start_color()
                        curses.use_default_colors()
                        self.screen = stdscr
                        curses.init_pair(1, curses.COLOR_GREEN, -1)
                        curses.init_pair(2, curses.COLOR_RED, -1)
                        curses.init_pair(3, curses.COLOR_BLUE, -1)
                        curses.init_pair(4, curses.COLOR_WHITE, -1)
                        self.screen.bkgd(' ', curses.color_pair(1))
                        self.screen.bkgd(' ')
                        curses.noecho()
                        curses.cbreak()
                        self.screen.keypad(1)
                        # curses.curs_set. 0 means invisible cursor, 1 visible, 2 very visible
                        curses.curs_set(0)
                        self.screen.addstr(0,0, 'Live Stream', curses.A_BOLD)
                        self.screen.refresh()
                        self.qscreen.task_done()

                    elif order == 'Stop':
                        self.screen.addstr(0,0, 'Press any key to go back to stf screen...                                                                   ', curses.A_BOLD)
                        self.screen.getstr(0,0, 15)
                        curses.nocbreak()
                        self.screen.keypad(0)
                        curses.echo()
                        curses.curs_set(1)
                        stdscr.refresh()
                        # close
                        self.qscreen.task_done()
                        curses.resetty()
                        self.f.close()
                        return
                    else:
                        #self.screen.addstr(0,50, 'Receiving Data')
                        self.screen.refresh()
                        # Get the screen size
                        (x_max, y_max) = self.screen.getmaxyx()
                        # The order 
                        orig_tuple = order
                        tuple_id = orig_tuple.get_id()
                        # Get the amount of letters that fit on the screen
                        state = orig_tuple.get_state()[-(y_max-self.y_min):]
                        tuple = self.get_tuple(tuple_id)
                        # Update the status bar
                        if int(tuple['x_pos']) < x_max - 3: 
                            self.screen.addstr(0,20,tuple_id + "                            ", curses.A_BOLD)
                            self.screen.refresh()
                            #self.screen.addstr(int(tuple['x_pos']), int(tuple['y_pos']), state, tuple['color'] | curses.A_BOLD)
                            #if int(tuple['x_pos']) <= xmax:
                            self.screen.addstr(int(tuple['x_pos']), int(tuple['y_pos']), state, tuple['color'])
                            #tuple['y_pos'] += len(state)
                            self.screen.refresh()
                            self.qscreen.task_done()
        except KeyboardInterrupt:
            curses.nocbreak()
            self.screen.keypad(0)
            curses.echo()
            curses.curs_set(1)
            curses.resetty()
            self.screen.refresh()
        except Exception as inst:
            print '\tProblem with Screen()'
            print type(inst)     # the exception instance
            print inst.args      # arguments stored in .args
            print inst           # __str__ allows args to printed directly
            sys.exit(1)


######################
######################
######################
class Visualizations(Module):
    ### Mandatory variables ###
    cmd = 'visualize_1'
    description = 'This module visualize the connections of a dataset.'
    authors = ['Sebastian Garcia']
    # Main dict of objects. The name of the attribute should be "main_dict" in this example
    main_dict = BTrees.OOBTree.BTree()
    ### End of Mandatory variables ###

    ### Mandatory Methods Don't change ###
    def __init__(self):
        # Call to our super init
        super(Visualizations, self).__init__()
        # Example of a parameter without arguments
        self.parser.add_argument('-v', '--visualize', metavar='datasetid', help='Visualize the connections in this dataset.')
        self.parser.add_argument('-x', '--multiplier', metavar='multiplier', type=float, default=0.0, help='Speed multiplier. 2 is twice, 3 is trice. -1 means to wait an equidistance but fake amount of time.')
        self.parser.add_argument('-f', '--filter', metavar='filter', nargs = '+', default="", help='Filter the connections to show. Keywords: name. Usage: name=<text> name!=<text>.  Partial matching.')
        # A local list of models
        self.models = {}

    def get_name(self):
        """ Return the name of the module"""
        return self.cmd

    # Mandatory Method! Don't change.
    def get_main_dict(self):
        """ Return the main dict where we store the info. Is going to the database"""
        return self.main_dict

    # Mandatory Method! Don't change.
    def set_main_dict(self, dict):
        """ Set the main dict where we store the info. From the database"""
        self.main_dict = dict
    ############ End of Mandatory Methods #########################


    def get_object(self, id):
        return self.main_dict[id]

    def get_objects(self):
        return self.main_dict.values()

    def visualize_dataset(self, dataset_id, multiplier, filter):
        # Get the netflow file
        self.dataset = __datasets__.get_dataset(dataset_id)
        try:
            self.binetflow_file = self.dataset.get_file_type('binetflow')
        except AttributeError:
            print_error('That testing dataset does no seem to exist.')
            return False
        # Open the file
        try:
            file = open(self.binetflow_file.get_name(), 'r')
            self.setup_screen()
        except IOError:
            print_error('The binetflow file is not present in the system.')
            return False
        # construct filter
        self.construct_filter(filter)
        # Clean the previous models from the constructor
        __modelsconstructors__.get_default_constructor().clean_models()
        # Remove the header
        header_line = file.readline().strip()
        # Find the separation character
        self.find_separator(header_line)
        # Extract the columns names
        self.find_columns_names(header_line)
        line = ','.join(file.readline().strip().split(',')[:14])
        #logfile = open('log','w')
        while line:
            # Using our own extract_columns function makes this module more independent
            column_values = self.extract_columns_values(line)
            # Extract its 4-tuple. Find (or create) the tuple object
            tuple4 = column_values['SrcAddr']+'-'+column_values['DstAddr']+'-'+column_values['Dport']+'-'+column_values['Proto']
            # Get the _local_ model. We don't want to mess with the real models in the database, but we need the structure to get the state
            model = self.get_model(tuple4)
            # filter
            if not self.apply_filter(tuple4):
                line = ','.join(file.readline().strip().split(',')[:14])
                continue
            if not model:
                model = Model(tuple4)
                self.set_model(model)
                constructor_id = __modelsconstructors__.get_default_constructor().get_id()
                # Warning, here we depend on the modelsconstrutor
                model.set_constructor(__modelsconstructors__.get_constructor(constructor_id))
            flow = Flow(0) # Fake flow id
            flow.add_starttime(column_values['StartTime'])
            flow.add_duration(column_values['Dur'])
            flow.add_proto(column_values['Proto'])
            flow.add_scraddr(column_values['SrcAddr'])
            flow.add_dir(column_values['Dir'])
            flow.add_dstaddr(column_values['DstAddr'])
            flow.add_dport(column_values['Dport'])
            flow.add_state(column_values['State'])
            flow.add_stos(column_values['sTos'])
            flow.add_dtos(column_values['dTos'])
            flow.add_totpkts(column_values['TotPkts'])
            flow.add_totbytes(column_values['TotBytes'])
            try:
                flow.add_srcbytes(column_values['SrcBytes'])
            except KeyError:
                # It can happen that we don't have the SrcBytes column
                pass
            try:
                flow.add_srcUdata(column_values['srcUdata'])
            except KeyError:
                # It can happen that we don't have the srcUdata column
                pass
            try:
                flow.add_dstUdata(column_values['dstUdata'])
            except KeyError:
                # It can happen that we don't have the dstUdata column
                pass
            try:
                flow.add_label(column_values['Label'])
            except KeyError:
                # It can happen that we don't have the label column
                pass
            # Add the flow
            model.add_flow(flow)
            # As fast as we can or with some delay?
            if multiplier != 0.0 and multiplier != -1:
                # Wait some time between flows. 
                last_time = model.get_last_flow_time()
                current_time = datetime.strptime(column_values['StartTime'], '%Y/%m/%d %H:%M:%S.%f')
                if last_time:
                    diff = current_time - last_time
                    wait_time = diff.total_seconds()
                    time.sleep(wait_time / multiplier)
                model.add_last_flow_time(current_time)
                # Wait the necessary time. After the visualization
            elif multiplier == -1:
                time.sleep(0.1)
            # Visualize this model
            self.qscreen.put(model)
            line = ','.join(file.readline().strip().split(',')[:14])
        self.qscreen.put('Stop')
        file.close()
        #logfile.close()

    def set_model(self, model):
        self.models[model.get_id()] = model

    def clean_models(self):
        self.models = {}

    def get_model(self, tuple_id):
        try:
            return self.models[tuple_id]
        except KeyError:
            return False

    def find_separator(self, line):
        count_commas = len(line.split(','))
        count_spaces = len(line.split(' '))
        if count_commas >= count_spaces:
            self.line_separator = ','
        elif count_spaces > count_commas:
            self.line_separator = ' '
        else:
            self.line_separator = ','

    def find_columns_names(self, line):
        """ Usually the columns in a binetflow file are 
        StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,srcUdata,dstUdata,Label
        """
        self.columns_names = line.split(self.line_separator)

    def extract_columns_values(self, line):
        """ Given a line text of a flow, extract the values for each column. The main difference with this function and the one in connections.py is that we don't use the src and dst data. """
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
        # Get the individual parts. We only support and's now.
        for part in filter:
            # Get the key
            try:
                key = re.split('<|>|=|\!=', part)[0]
                value = re.split('<|>|=|\!=', part)[1]
            except IndexError:
                # No < or > or = or != in the string. Just stop.
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
            # We should search for != before =
            try:
                part.index('!=')
                operator = '!='
            except ValueError:
                # Now we search for =
                try:
                    part.index('=')
                    operator = '='
                except ValueError:
                    pass
            self.filter.append((key, operator, value))

    def apply_filter(self, tuple4):
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
                # For filtering based on the label assigned to the model with stf (contrary to the flow label)
                if operator == '=':
                    if value in tuple4:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '!=':
                    if value not in tuple4:
                        responses.append(True)
                    else:
                        responses.append(False)
            else:
                return False
        for response in responses:
            if not response:
                return False
        return True

    def setup_screen(self):
        # Create the queue             
        self.qscreen = JoinableQueue()
        # Create the thread            
        self.screenThread = Screen(self.qscreen)
        self.screenThread.start()           
        # Waint until the screen is initialized
        # First send the message       
        self.qscreen.put('Start')
        # Then wait for an answer      
        self.qscreen.join()      

    # The run method runs every time that this command is used. Mandatory
    def run(self):
        ######### Mandatory part! don't delete ########################
        # Register the structure in the database, so it is stored and use in the future. 
        if not __database__.has_structure(Visualizations().get_name()):
            print_info('The structure is not registered.')
            __database__.set_new_structure(Visualizations())
        else:
            main_dict = __database__.get_new_structure(Visualizations())
            self.set_main_dict(main_dict)

        # List general help. Don't modify.
        def help():
            self.log('info', self.description)

        # Run
        super(Visualizations, self).run()
        if self.args is None:
            return
        ######### End Mandatory part! ########################
        

        # Process the command line and call the methods. Here add your own parameters
        if self.args.visualize:
            self.visualize_dataset(int(self.args.visualize), self.args.multiplier, self.args.filter)
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()
