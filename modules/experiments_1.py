# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# This is a template module showing how to create a module that has persistence in the database. To create your own command just copy this file and start modifying it.

import persistent
import BTrees.OOBTree

from stf.common.out import *
from stf.common.abstracts import Module
from stf.core.models import  __groupofgroupofmodels__ 
from stf.core.dataset import __datasets__
from stf.core.notes import __notes__
from stf.core.connections import  __group_of_group_of_connections__
from stf.core.models_constructors import __modelsconstructors__ 
from stf.core.labels import __group_of_labels__
from stf.core.database import __database__
from modules.markov_models_1 import __group_of_markov_models__

from datetime import datetime
from datetime import timedelta
import time


######################
######################
######################
class Tuple(object):
    """ The class to simply handle tuples """
    def __init__(self,tuple4):
        self.id = tuple4
        self.ground_truth_label = ""
        self.datetime = ""
        self.amount_of_flows = 0

    def add_new_flow(self, column_values):
        """ Add new stuff about the flow in this tuple """
        # The ground truth label should be taken from the label object
        self.ground_truth_label = column_values['Label']
        #self.ground_truth_label = "To Be Defined"
        self.datetime = column_values['StartTime']
        self.amount_of_flows += 1

    def get_id(self):
        return self.id

    def get_summary(self):
        """ A summary of what happened in this tuple """
        return 'Tuple: {}, Amount of flows: {}'.format(self.id, self.amount_of_flows)
    
    def __repr__(self):
        return('Id: {}, Label:{}, Datetime: {}'.format(self.get_id(), self.ground_truth_label, self.datetime))



######################
######################
######################
class TimeSlot(persistent.Persistent):
    """ Class to work with the time slots of results from the testing """
    def __init__(self, time, width):
        self.init_time = time 
        self.finish_time = self.init_time + timedelta(seconds=width)
        self.ip_dict = {}
        self.time_slot_width = width

    def add_label_for_ip(self, ip, label):
        """ Get an ip and a label, and decide if it should be changed, assigned or what """
        return True

    def close(self):
        """ Close the slot """
        #  - Compute the errors (TP, TN, FN, FP) for all the IPs in this time slot.
        #  - Compute the performance metrics in this time slot.
        #  - Compute the performance metrics so far (average?)
        #  - Store the results in the results_dict
        pass

    def __repr__(self):
        return ('TimeSlot start: {}, ends: {}'.format(self.init_time, self.finish_time))




######################
######################
######################
class Experiment(persistent.Persistent):
    """ An individual experiment """
    def __init__(self, id, description):
        self.id = id
        self.description = description
        # Dict of tuples in this experiment during testing
        self.tuples = {}
        # The vect of time slots
        self.time_slots = []
        self.time_slot_width = 300.0 # Now we hardcoded 300 seconds (5 mins), but it should be selected by the user
        print_info('Using the default model constructor for the testing netflow. If you need, change it.')

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def set_description(self, description):
        self.description = description

    def get_description(self):
        return self.description

    def delete(self):
        return True

    def add_models_ids(self, models_ids):
        self.models_ids = models_ids

    def add_testing_id(self, testing_id):
        self.testing_id = testing_id

    def run(self):
        """ Run the experiment """
        # Train the models
        print_info('Models for detection: {}'.format(self.models_ids))
        group_mm = __group_of_markov_models__
        # This is necessary to get the models correctly from outside the class
        group_mm.run() 
        # Convert the str to int
        self.models_ids = map(int, self.models_ids.split(','))
        for model_id in self.models_ids:
            print_info('\tTraining model {}'.format(model_id))
            group_mm.train(model_id, "", self.models_ids, True)
        # Methodology 2. Train the thresholds of the training models between themselves
        # Methodology 3. Start the testing
        # Methodology 3.1. Get the binetflow file
        test_dataset = __datasets__.get_dataset(self.testing_id)
        self.file_obj = test_dataset.get_file(1)
        # Methodology 3.2. Create the dictionary for holding the labels info (IPs are key, data is another dict with time slots as key, data is label)
        self.labels_dict = {}
        # Methodology 3.3. Create the dictionary for holding the IP info (time slots are key, then all the errors and performance metrics in a vector)
        self.results_dict = {}
        print_info('Testing with the netflow file: {}'.format(self.file_obj.get_name()))
        # Methodology 3.2. Process the netflow file for testing
        self.process_netflow_for_testing()

    def get_time_slot(self, column_values):
        """ Get the columns values and return the correct time slot object. Also closes the old time slot """
        starttime = datetime.strptime(column_values['StartTime'], '%Y/%m/%d %H:%M:%S.%f') 
        # Find the slot for this flow (theoretically it works with unordered flows)
        for slot in reversed(self.time_slots):
            if starttime >= slot.init_time and starttime <= slot.finish_time:
                return slot
        # Methodology 4.4. The first flow case and the case where the flow should be in a new flow because it is outside the last slot. All in one!
        new_slot = TimeSlot(starttime, self.time_slot_width)
        #print_info('New Slot Time: {}'.format(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))
        # Add it
        self.time_slots.append(new_slot)
        if self.time_slots:
            # We created a slot because the flow is outside the width, so we should close the previous time slot
            # Closethe last slot
            self.time_slots[-1].close()
        return new_slot

    def process_netflow_for_testing(self):
        """ Get a netflow file and process it for testing """
        file = open(self.file_obj.get_name(), 'r')
        # Remove the header
        header_line = file.readline().strip()
        # Find the separation character
        self.find_separator(header_line)
        # Extract the columns names
        self.find_columns_names(header_line)
        line = file.readline().strip()
        # Methodology 4. For each flow
        print_info('Time: {}'.format(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))
        group_group_of_models = __groupofgroupofmodels__ 
        # The constructor of models can change. Now we hardcode -1, but warning!
        group_id = str(self.testing_id) + '-1'
        group_of_models = group_group_of_models.get_group(group_id)
        while line:
            # Extract the column values
            column_values = self.extract_columns_values(line)
            # Methodology 4.1. Extract its 4-tuple. Find (or create) the tuple object
            tuple = self.get_tuple(column_values)
            # Methodology 4.2. Add all the relevant data to this tupple
            tuple.add_new_flow(column_values)
            #print 'Tuple: {}'.format(tuple)
            # Methodology 4.3. Get the correct time slot
            time_slot = self.get_time_slot(column_values)
            #print 'Assigned to time slot: {}'.format(time_slot)
            # Methodology 4.4 Get the letter for this flow.
            model = group_of_models.get_model(tuple.get_id())
            state_so_far = model.get_state()[0:tuple.amount_of_flows]
            # HERE
            # Read next line
            line = file.readline().strip()
        # Close the file
        file.close()
        print_info('Time: {}'.format(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))
        # Print something about all the tuples
        print 'Total amount of tuples: {}'.format(len(self.tuples))
        print 'Total time slots: {}'.format(len(self.time_slots))

        #       - Store this letter in its 4-tuple.
        #       - Compute the distance of the chain of states from this 4-tuple so far, with all the training models. Don't store a new distance object.
        #       - Decide upon a winner model.
        #       - Obtain the label of the winner model.
        #       - From the labels_dict, search the IP, search the current time slot and extract the current label.
        #       - See if we should change the current label. If so, change it.
        #   - When the netflow file finishes
        #       - compute the results of the last time slot
        #       - Select the combination of training models that had the better performance metrics for this testing dataset.
        #       - Print the winner performance metric and the winner combination of models.

    def get_tuple(self, column_values):
        """ Get the values and return the correct tuple for them """
        tuple4 = column_values['SrcAddr']+'-'+column_values['DstAddr']+'-'+column_values['Dport']+'-'+column_values['Proto']
        try:
            tuple = self.tuples[tuple4]
            # We already have this connection
        except KeyError:
            # First time for this connection
            tuple = Tuple(tuple4)
            self.tuples[tuple4] = tuple
        return tuple

    def find_columns_names(self, line):
        """ Usually the columns in a binetflow file are 
        StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,srcUdata,dstUdata,Label
        """
        self.columns_names = line.split(self.line_separator)
            
    def find_separator(self, line):
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

    # Mandatory __repr__ module. Something you want to identify each object with. Usefull for selecting objects later
    def __repr__(self):
        return('Id:' + str(self.get_id()))




    


######################
######################
######################
class Group_of_Experiments(Module, persistent.Persistent):
    """ The group of Experiments """
    ### Mandatory variables ###
    cmd = 'experiments_1'
    description = 'Creates experiments with trained models on testing datasets.'
    authors = ['Sebastian Garcia']
    # Main dict of objects. The name of the attribute should be "main_dict" in this example
    main_dict = BTrees.OOBTree.BTree()
    ### End of Mandatory variables ###

    ### Mandatory Methods Don't change ###
    def __init__(self):
        # Call to our super init
        super(Group_of_Experiments, self).__init__()
        # Example of a parameter without arguments
        self.parser.add_argument('-l', '--list', action='store_true', help='List the Experiments.')
        # Example of a parameter with arguments
        self.parser.add_argument('-p', '--printstate', metavar='experiment_id', help='Print some info about the experiment.')
        self.parser.add_argument('-n', '--new', action='store_true', help='Create a new experiment. Use -m to assign the models to use for detection. Use -t to select a testing dataset.')
        self.parser.add_argument('-d', '--delete', metavar='delete', help='Delete an experiment given the id.')
        self.parser.add_argument('-m', '--models_ids', metavar='models_ids', help='Ids of the models (e.g. Markov Models) to be used when creating a new experiment with -n. Comma separated.')
        self.parser.add_argument('-t', '--testing_id', metavar='testing_id', type=int, help='Dataset id to be used as testing when creating a new experiment with -n.')

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


    def get_experiment(self, id):
        return self.main_dict[id]

    def get_experiments(self):
        return self.main_dict.values()

    def list_experiments(self):
        print_info('List of objects')
        rows = []
        for object in self.get_experiments():
            rows.append([ object.get_id(), object.get_description() ])
        print(table(header=['Id', 'Description'], rows=rows))

    def create_new_experiment(self, models_ids, testing_id):
        """ Create a new experiment """
        # Generate the new id
        try:
            new_id = self.main_dict[list(self.main_dict.keys())[-1]].get_id() + 1
        except (KeyError, IndexError):
            new_id = 1
        # Set the description
        desc = raw_input("Description: ")
        # Create the new object
        new_experiment = Experiment(new_id, desc)
        # Methodology 1. We receive the markov_models ids for the training, and the id of the dataset of the tetsing. (We may not have markov models for the testing. A binetflow file and labels are enough)
        # Add info
        new_experiment.add_models_ids(models_ids)
        new_experiment.add_testing_id(testing_id)
        # Store on DB
        self.main_dict[new_id] = new_experiment
        # Run it
        new_experiment.run()



    def delete_experiment(self, id):
        """ Deletes an experiment """
        ans = raw_input('Are you sure you want to delete experiment {} (YES/NO)?: '.format(id))
        if ans == "YES":
            # Get the experiment
            exp = self.get_experiment(id)
            # First delete everything inside the experiment
            exp.delete()
            # Now delete it from the list of experiments
            self.main_dict.pop(id)

    # The run method runs every time that this command is used. Mandatory
    def run(self):
        ######### Mandatory part! don't delete ########################
        # Register the structure in the database, so it is stored and use in the future. 
        if not __database__.has_structure(Group_of_Experiments().get_name()):
            print_info('The structure is not registered.')
            __database__.set_new_structure(Group_of_Experiments())
        else:
            main_dict = __database__.get_new_structure(Group_of_Experiments())
            self.set_main_dict(main_dict)

        # List general help. Don't modify.
        def help():
            self.log('info', self.description)

        # Run
        super(Group_of_Experiments, self).run()
        if self.args is None:
            return
        ######### End Mandatory part! ########################
        

        # Process the command line and call the methods. Here add your own parameters
        if self.args.list:
            self.list_experiments()
        elif self.args.new:
            try:
                models_ids = self.args.models_ids
                testing_id = self.args.testing_id
            except AttributeError:
                print_error('You should provide both the ids of the models to use for detection (with -m) and the testing dataset id (with -t).')
                return False
            self.create_new_experiment(models_ids, testing_id)
        elif self.args.delete:
            self.delete_experiment(int(self.args.delete))
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()
