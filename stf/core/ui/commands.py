# This file is part of the Stratosphere Testing Framework 
# See the file 'LICENSE' for copying permission.
# Most of this file is copied from Viper

import argparse
import os
import time
import fnmatch
import tempfile
import shutil
import transaction

from stf.common.out import *
from stf.core.dataset import __datasets__
from stf.core.experiment import __experiments__
from stf.core.database import __database__
from stf.core.connections import __group_of_group_of_connections__
from stf.core.models_constructors import __modelsconstructors__
from stf.core.models import __groupofgroupofmodels__

class Commands(object):

    def __init__(self):
        # Map commands to their related functions.
        self.commands = dict(
            help=dict(obj=self.cmd_help, description="Show this help message"),
            info=dict(obj=self.cmd_info, description="Show information on the opened experiment"),
            clear=dict(obj=self.cmd_clear, description="Clear the console"),
            experiments=dict(obj=self.cmd_experiments, description="List or switch to existing experiments"),
            datasets=dict(obj=self.cmd_datasets, description="Manage the datasets"),
            connections=dict(obj=self.cmd_connections, description="Manage the connections. A dataset should be selected first."),
            models=dict(obj=self.cmd_models, description="Manage the models. A dataset should be selected first."),
            database=dict(obj=self.cmd_models, description="Manage the models. A dataset should be selected first."),
            exit=dict(obj=self.cmd_exit, description="Exit"),
        )

    ##
    # CLEAR
    #
    # This command simply clears the shell.
    def cmd_clear(self, *args):
        os.system('clear')

    ##
    # HELP
    #
    # This command simply prints the help message.
    # It lists both embedded commands and loaded modules.
    def cmd_help(self, *args):
        print(bold("Commands:"))

        rows = []
        for command_name, command_item in self.commands.items():
            rows.append([command_name, command_item['description']])

        #rows.append(["exit, quit", "Exit Viper"])
        rows = sorted(rows, key=lambda entry: entry[0])

        print(table(['Command', 'Description'], rows))
        #print("")
        #print(bold("Modules:"))

        #rows = []
        #for module_name, module_item in __modules__.items():
            #rows.append([module_name, module_item['description']])

        #rows = sorted(rows, key=lambda entry: entry[0])

        #print(table(['Command', 'Description'], rows))



    ##
    # INFO
    #
    # This command returns information on the open experiment.
    def cmd_info(self, *args):
        if __experiments__.is_set() and __experiments__.current:
            print_info('Information about the current experiment')
            print(table(
                ['Name', 'Value'],
                [
                    ('Name', __experiments__.current.get_name()),
                ]
            ))
        else:
            print_info('There is no current experiment')


    ##
    # MODELS
    #
    # This command works with models
    def cmd_models(self, *args):
        parser = argparse.ArgumentParser(prog="models", description="Manage models", epilog="Manage models")
        parser.add_argument('-c', '--listconstructors', action="store_true", help="List all models constructors available.")
        parser.add_argument('-l', '--listgroups', action="store_true", help="List all the groups of  models. If a dataset is selected it only shows the models in that dataset.")
        parser.add_argument('-g', '--generate', action="store_true", help="Generate the models for the current dataset.")
        parser.add_argument('-d', '--deletegroup', metavar="group_model_id", help="Delete a group of models.")
        parser.add_argument('-D', '--deletemodelbyid', metavar="model_id", help="Delete a specific model from the group given the id. The id is the 4-tuple of the model.")
        parser.add_argument('-L', '--listmodels', metavar="group_model_id", help="List the models inside a group.")
        parser.add_argument('-C', '--countmodels', metavar="group_model_id", help="Count the models inside a group.")
        parser.add_argument('-E', '--deletemodelbyfilter', metavar="model_id", help="Delete a specific model from the group given a filter.")
        parser.add_argument('-f', '--filter', metavar="filter", nargs = '+', help="Use this filter to work with models. Format: \"variable[=<>]value\". You can use the variables: statelen, nameincludes. For example: -f statelen>100 nameincludes=tcp.")


        try:
            args = parser.parse_args(args)
        except:
            return

        # Subcomand to list the constructors
        if args.listconstructors:
            __modelsconstructors__.list_constructors()

        # Subcomand to list the models
        elif args.listgroups:
            __groupofgroupofmodels__.list_groups()

        # Subcomand to generate the models
        elif args.generate:
            __groupofgroupofmodels__.generate_group_of_models()
            __database__.root._p_changed = True

        # Subcomand to delete the group of models of the current dataset
        elif args.deletegroup:
            __groupofgroupofmodels__.delete_group_of_models(int(args.deletegroup))
            __database__.root._p_changed = True

        # Subcomand to list the models in a group
        elif args.listmodels:
            filter = ''
            try:
                filter = args.filter

            except AttributeError:
                pass
            __groupofgroupofmodels__.list_models_in_group(int(args.listmodels), filter)
            __database__.root._p_changed = True

        # Subcomand to delete a model from a group by id
        elif args.deletemodelbyid:
            __groupofgroupofmodels__.delete_a_model_from_the_group_by_id(args.deletemodel)
            __database__.root._p_changed = True

        # Subcomand to delete a model from a group by filter
        elif args.deletemodelbyfilter:
            filter = ''
            try:
                filter = args.filter
            except AttributeError:
                print_error('No filter specified. If you want to delete all the models use -d')
                return
            __groupofgroupofmodels__.delete_a_model_from_the_group_by_filter(filter)
            __database__.root._p_changed = True

        # Subcomand to count the amount of models
        elif args.countmodels:
            try:
                filter = args.filter
            except AttributeError:
                pass
            __groupofgroupofmodels__.count_models_in_group(args.countmodels, filter)
            __database__.root._p_changed = True

    ##
    # CONNECTIONS
    #
    # This command works with connections
    def cmd_connections(self, *args):
        parser = argparse.ArgumentParser(prog="connections", description="Manage connnections", epilog="Manage connections")
        parser.add_argument('-l', '--list', action="store_true", help="List all existing connections")
        parser.add_argument('-g', '--generate', action="store_true", help="Generate the connections from the binetflow file in the current dataset")
        parser.add_argument('-d', '--delete', metavar="group_of_connections_id", help="Delete the group of connections.")
        parser.add_argument('-L', '--listconnections', metavar="group_connection_id", help="List the connections inside a group.")
        parser.add_argument('-F', '--showflows', metavar="connection_id", type=str, help="List the flows inside a specific connection.")
        parser.add_argument('-f', '--filter', metavar="filter", nargs='+', help="Use this filter to work with connections. Format: \"variable[=<>]value\". You can use the variables: nameincludes. Example: \"nameincludes=tcp\".")
        try:
            args = parser.parse_args(args)
        except:
            return

        # Subcomand to list
        if args.list:
            __group_of_group_of_connections__.list_group_of_connections()

        # Subcomand to create a new group of connections
        elif args.generate:
            # We should have a current dataset
            if not __datasets__.current:
                print_error('You should first select a dataset with datasets -s <id>')
                return False
            # We should have a binetflow file in the dataset
            binetflow_file = __datasets__.current.get_file_type('binetflow')
            if binetflow_file:
                __group_of_group_of_connections__.create_group_of_connections(binetflow_file.get_name(), __datasets__.current.get_id(), binetflow_file.get_id() )
                __database__.root._p_changed = True
            else:
                print_error('You should have a binetflow file in your dataset')
                return False

        # Subcomand to delete a group of connections
        elif args.delete:
            __group_of_group_of_connections__.del_group_of_connections(int(args.delete))
            __database__.root._p_changed = True

        # Subcomand to list the connections in a group
        elif args.listconnections:
            filter = ''
            try:
                filter = args.filter
            except AttributeError:
                pass
            __group_of_group_of_connections__.list_connections_in_group(int(args.listconnections), filter)
            __database__.root._p_changed = True
            
        # Subcomand to show the flows in a connection
        elif args.showflows:
            filter = ''
            try:
                filter = args.filter
            except AttributeError:
                pass
            __group_of_group_of_connections__.show_flows_in_connnection(args.showflows, filter)
            __database__.root._p_changed = True


    ##
    # DATASETS
    #
    # This command works with datasets
    def cmd_datasets(self, *args):
        parser = argparse.ArgumentParser(prog="datasets", description="Manage datasets", epilog="Manage datasets")
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-l', '--list', action="store_true", help="List all existing datasets.")
        group.add_argument('-c', '--create', metavar='filename', help="Create a new dataset from a file.")
        group.add_argument('-d', '--delete', metavar='dataset_id', help="Delete a dataset.")
        group.add_argument('-s', '--select', metavar='dataset_id', help="Select a dataset to work with. Enables the following commands on the dataset.")
        group.add_argument('-f', '--list_files', action='store_true', help="List all the files in the current dataset")
        group.add_argument('-F', '--file', metavar='file_id', help="Give more info about the selected file in the current dataset.")
        group.add_argument('-a', '--add', metavar='file_id', help="Add a file to the current dataset.")
        group.add_argument('-D', '--dele', metavar='file_id', help="Delete a file from the dataset.")
        group.add_argument('-g', '--generate', action='store_true', help="Try to generate the biargus and binetflow files for the selected dataset if they do not exists.")
        group.add_argument('-u', '--unselect', action='store_true', help="Unselect the current dataset.")

        try:
            args = parser.parse_args(args)
        except:
            return

        # Subcomand to list
        if args.list:
            __datasets__.list()

        # Subcomand to create
        elif args.create:
            __datasets__.create(args.create)
            __database__.root._p_changed = True

        # Subcomand to delete
        elif args.delete:
            __datasets__.delete(args.delete)
            __database__.root._p_changed = True

        # Subcomand to select a dataset
        elif args.select :
            __datasets__.select(args.select)

        # Subcomand to list files
        elif args.list_files:
            __datasets__.list_files()
            __database__.root._p_changed = True

        # Subcomand to get info about a file in a dataset
        elif args.file :
            __datasets__.info_about_file(args.file)
            __database__.root._p_changed = True

        # Subcomand to add a file to the dataset
        elif args.add :
            __datasets__.add_file(args.add)
            __database__.root._p_changed = True

        # Subcomand to delete a file from the dataset
        elif args.dele :
            __datasets__.del_file(args.dele)
            __database__.root._p_changed = True

        # Subcomand to generate the biargus and binetflow files in a  dataset
        elif args.generate :
            __datasets__.generate_argus_files()
            __database__.root._p_changed = True

        # Subcomand to unselect the current dataset
        elif args.unselect :
            __datasets__.unselect_current()

        else:
            parser.print_usage()



    ##
    # EXPERIMENTS
    #
    # This command retrieves a list of all experiments.
    # You can also switch to a different experiments.
    def cmd_experiments(self, *args):
        parser = argparse.ArgumentParser(prog="experiments", description="Manage experiments", epilog="Manage experiments")
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-l', '--list', action="store_true", help="List all existing experiments")
        group.add_argument('-s', '--switch', metavar='experiment_name', help="Switch to the specified experiment")
        group.add_argument('-c', '--create', metavar='experiment_name', help="Create a new experiment")
        group.add_argument('-d', '--delete', metavar='experiment_id', help="Delete an experiment")

        try:
            args = parser.parse_args(args)
        except:
            return

        # Subcomand to list
        if args.list:
            __experiments__.list_all()

        # Subcomand to switch
        elif args.switch:
            __experiments__.switch_to(args.switch)

        # Subcomand to create
        elif args.create:
            __experiments__.create(args.create)
            __database__.root._p_changed = True

        # Subcomand to delete
        elif args.delete:
            __experiments__.delete(args.delete)
            __database__.root._p_changed = True

        else:
            parser.print_usage()

    ##
    # EXIT
    #
    def cmd_exit(self):
        # Exit is handled in other place. This is so it can appear in the autocompletion
        pass

