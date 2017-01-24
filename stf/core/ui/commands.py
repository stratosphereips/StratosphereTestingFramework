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
#from stf.core.experiment import __experiments__
from stf.core.database import __database__
from stf.core.connections import __group_of_group_of_connections__
from stf.core.models_constructors import __modelsconstructors__
from stf.core.models import __groupofgroupofmodels__
from stf.core.notes import __notes__
from stf.core.labels import __group_of_labels__ 
from stf.core.plugins import __modules__

class Commands(object):

    def __init__(self):
        # Map commands to their related functions.
        self.commands = dict(
            help=dict(obj=self.cmd_help, description="Show this help message"),
            #info=dict(obj=self.cmd_info, description="Show information on the opened experiment"),
            clear=dict(obj=self.cmd_clear, description="Clear the console"),
            #experiments=dict(obj=self.cmd_experiments, description="List or switch to existing experiments"),
            datasets=dict(obj=self.cmd_datasets, description="Manage the datasets"),
            connections=dict(obj=self.cmd_connections, description="Manage the connections. A dataset should be selected first."),
            models=dict(obj=self.cmd_models, description="Manage the models. A dataset should be selected first."),
            database=dict(obj=self.cmd_database, description="Manage the database."),
            notes=dict(obj=self.cmd_notes, description="Manage the notes."),
            labels=dict(obj=self.cmd_labels, description="Manage the labels."),
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
        print("")
        print(bold("Modules:"))

        rows = []
        for module_name, module_item in __modules__.items():
            rows.append([module_name, module_item['description']])

        rows = sorted(rows, key=lambda entry: entry[0])

        print(table(['Command', 'Description'], rows))

    ##
    # NOTES
    #
    # This command works with notes
    def cmd_notes(self, *args):
        parser = argparse.ArgumentParser(prog="notes", description="Manage notes", epilog="Manage notes")
        parser.add_argument('-l', '--listnotes', action="store_true", help="List all the notes in the system.")
        parser.add_argument('-d', '--deletenote', metavar="note_id", help="Delete a note.")
        parser.add_argument('-f', '--filter', metavar="filter", nargs = '+', help="Use this filter to work with notes. You can use multiple filter separated by a space. Format: \"variable[=<>]value\". You can use the variables: text. For example: -f text=hi text!=p2p.")
        parser.add_argument('-s', '--show', type=int, metavar="note_id", help="Show this note id.")
        parser.add_argument('-e', '--edit', type=int, metavar="note_id", help="Edit this note id.")
        parser.add_argument('-S', '--search', type=str, metavar="text", help="Search a text in all the notes, and list the notes.")


        try:
            args = parser.parse_args(args)
        except:
            return

        # Subcomand to list the notes
        if args.listnotes:
            __notes__.list_notes()

        # Subcomand to delte a note
        elif args.deletenote:
            __notes__.delete_note(int(args.deletenote))
            __database__.root._p_changed = True

        # Subcomand to show a note
        elif args.show:
            __notes__.show_note(args.show)

        # Subcomand to edit a note
        elif args.edit >= 0:
            __notes__.edit_note(args.edit)
            __database__.root._p_changed = True

        # Subcomand to search a text
        elif args.search:
            __notes__.search_text(args.search)

    ##
    # MODELS
    #
    # This command works with models
    def cmd_models(self, *args):
        parser = argparse.ArgumentParser(prog="models", description="Manage models", epilog="Manage models")
        parser.add_argument('-s', '--listconstructors', action="store_true", help="List all models constructors available.")
        parser.add_argument('-l', '--listgroups', action="store_true", help="List all the groups of  models. If a dataset is selected it only shows the models in that dataset.")
        parser.add_argument('-g', '--generate', action="store_true", help="Generate the models for the current dataset.")
        parser.add_argument('-d', '--deletegroup', metavar="group_model_id", help="Delete a group of models.")
        parser.add_argument('-D', '--deletemodel', metavar="group_model_id", help="Delete a model (4tuple) from this group. With -D give the id of the group. Use -i to give the model id to delete (4-tuple) or -f to use a filter.")
        parser.add_argument('-i', '--modelid', metavar="model_id", help="Use this model id (4-tuple). Commonly used with -D.")
        parser.add_argument('-L', '--listmodels', metavar="group_model_id", help="List the models inside a group. You can use filters.")
        parser.add_argument('-C', '--countmodels', metavar="group_model_id", help="Count the models inside a group.")
        parser.add_argument('-f', '--filter', metavar="filter", nargs = '+', default="", help="Use this filter to work with models. You can use multiple filter separated by a space. Format: \"variable[=<>]value\". You can use the variables: statelength, name and labelname. For example: -f statelength>100 name=tcp. Another example: -f name=-tcp- labelname=Botnet")
        parser.add_argument('-H', '--histogram', metavar="group_model_id", help="Plot a histogram of the lengths of models states in the given id of group of models.")
        parser.add_argument('-N', '--delnote', metavar='group_model_id', help="Delete completely the note related with this model id. Use -i to give the model id to add the note to (4-tuple).")
        parser.add_argument('-n', '--editnote', metavar='group_model_id', help="Edit the note related with this model id. Use -i to give the model id to add the note to (4-tuple).")
        parser.add_argument('-o', '--listnotes', default=0,  metavar='group_model_id', help="List the notes related with this model id. You can use the -f with filters here.")
        parser.add_argument('-a', '--amountoflettersinstate', default=0, metavar='amount_of_letters', help="When used with -L, limit the maximum amount of letters in the state to show per line. Helps avoiding dangerously long lines.")
        parser.add_argument('-c', '--constructor', metavar="constructor_id", type=int, help="Use this constructor for generating the new models. Use optionally with -g.")
        parser.add_argument('-e', '--exportasciimodels', metavar="group_model_id", help="Export an ascii list of the all the connections, labels and letters in this Model id. Useful for external analysis.")


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
            if args.constructor != None:
                if __modelsconstructors__.has_constructor_id(args.constructor):
                    constructor = int(args.constructor)
                else:
                    print_error('No such constructor id available.')
                    return False
            else:
                constructor = __modelsconstructors__.get_default_constructor().get_id()
            __groupofgroupofmodels__.generate_group_of_models(constructor)
            __database__.root._p_changed = True

        # Subcomand to delete the group of models of the current dataset
        elif args.deletegroup:
            __groupofgroupofmodels__.delete_group_of_models(args.deletegroup)
            __database__.root._p_changed = True

        # Subcomand to list the models in a group
        elif args.listmodels:
            __groupofgroupofmodels__.list_models_in_group(args.listmodels, args.filter, int(args.amountoflettersinstate))

        # Subcommand to export the ascii of the models
        elif args.exportasciimodels:
            __groupofgroupofmodels__.export_models_in_group(args.exportasciimodels, args.filter)

        # Subcomand to delete a model from a group by id or filter
        elif args.deletemodel:
            # By id or filter?
            if args.modelid:
                # By id
                __groupofgroupofmodels__.delete_a_model_from_the_group_by_id(args.deletemodel, args.modelid)
                __database__.root._p_changed = True
            elif args.filter:
                # By filter
                __groupofgroupofmodels__.delete_a_model_from_the_group_by_filter(args.deletemodel, args.filter)
                __database__.root._p_changed = True
            else:
                print_error('You should provide the id of the model (4-tuple) with -i or a filter with -f')

        # Subcomand to count the amount of models
        elif args.countmodels:
            __groupofgroupofmodels__.count_models_in_group(args.countmodels, args.filter)
            __database__.root._p_changed = True

        # Subcomand to plot histogram of states lengths
        elif args.histogram:
            __groupofgroupofmodels__.plot_histogram(args.histogram, args.filter)

        # Subcomand to edit the note of this model
        elif args.editnote:
            if args.modelid:
                __groupofgroupofmodels__.edit_note(args.editnote, args.modelid)
                __database__.root._p_changed = True
            else:
                print_error('You should give a model id also with -i.')
            
        # Subcomand to delete the note of this model
        elif args.delnote :
            if args.modelid:
                __groupofgroupofmodels__.del_note(args.delnote, args.modelid)
                __database__.root._p_changed = True
            else:
                print_error('You should give a model id also with -i.')

        # Subcomand to list the note of this model
        elif args.listnotes :
            __groupofgroupofmodels__.list_notes(args.listnotes, args.filter)
            __database__.root._p_changed = True

    ##
    # CONNECTIONS
    #
    # This command works with connections
    def cmd_connections(self, *args):
        parser = argparse.ArgumentParser(prog="connections", description="Manage connections", epilog="Manage connections")
        parser.add_argument('-l', '--list', action="store_true", help="List all existing connections")
        parser.add_argument('-g', '--generate', action="store_true", help="Generate the connections from the binetflow file in the current dataset")
        parser.add_argument('-d', '--delete', metavar="group_of_connections_id", help="Delete the group of connections.")
        parser.add_argument('-L', '--listconnections', metavar="group_connection_id", help="List the connections inside a group.")
        parser.add_argument('-F', '--showflows', metavar="connection_id", type=str, help="List the flows inside a specific connection.")
        parser.add_argument('-f', '--filter', metavar="filter", nargs='+', help="Use this filter to work with connections. Format: \"variable[!=<>]value\". You can use the variables: name, flowamount. Example: \"name=tcp\". Or \"flowamount<10\"")
        parser.add_argument('-D', '--deleteconnection', metavar="group_connection_id", help="Delete a connection from the group. This is the id of the group. Use -i to give the connection id to delete (4-tuple) or -f to use a filter.")
        parser.add_argument('-i', '--connectionid', metavar="connection_id", help="Use this connection id (4-tuple). Commonly used with -D.")
        parser.add_argument('-M', '--deleteconnectionifmodel', metavar="group_connection_id", help="Delete the connections from the group which models were deleted. Only give the connection group id. Useful to clean the  database of connections that are not used.")
        parser.add_argument('-t', '--trimgroupid', metavar="group_connection_id", help="Trim all the connections so that each connection has at most 100 flows. Only give the connection group id. Useful to have some info about the connections but not all the data.")
        parser.add_argument('-a', '--amounttotrim', metavar="amount_to_trim", type=int, help="Define the amount of flows to trim with -t. By default 100.")
        parser.add_argument('-C', '--countconnections', metavar="group_connection_id", help="Count the amount of connections matching the filter. This is the id of the group.")
        parser.add_argument('-H', '--histogram', metavar="connection_id", type=str, help="Show the histograms for state len, duration and size of all the flows in this connection id (4-tuple).")
        try:
            args = parser.parse_args(args)
        except:
            return

        # Subcomand to list
        if args.list:
            __group_of_group_of_connections__.list_group_of_connections()

        # Subcomand to create a new group of connections
        elif args.generate:
                __group_of_group_of_connections__.create_group_of_connections()
                __database__.root._p_changed = True

        # Subcomand to delete a group of connections
        elif args.delete:
            __group_of_group_of_connections__.delete_group_of_connections(int(args.delete))
            __database__.root._p_changed = True

        # Subcomand to list the connections in a group
        elif args.listconnections:
            filter = ''
            try:
                filter = args.filter
            except AttributeError:
                pass
            try:
                __group_of_group_of_connections__.list_connections_in_group(int(args.listconnections), filter)
            except ValueError:
                print_error('The id of the group of connections should be an integer.')
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

        # Subcomand to delete a connection from a group by id 
        elif args.deleteconnection:
            if args.connectionid:
                # By id
                __group_of_group_of_connections__.delete_a_connection_from_the_group_by_id(args.deleteconnection, args.connectionid)
            elif args.filter:
                __group_of_group_of_connections__.delete_a_connection_from_the_group_by_filter(args.deleteconnection, args.filter)
            __database__.root._p_changed = True

        # Subcomand to delete the connections from a group which models were deleted
        elif args.deleteconnectionifmodel:
            __group_of_group_of_connections__.delete_a_connection_from_the_group_if_model_deleted(int(args.deleteconnectionifmodel))
            __database__.root._p_changed = True

        # Subcomand to trim the amount of flows in the connections
        elif args.trimgroupid:
            # Now just trim to keep 100 flows
            if args.amounttotrim:
                amount_to_trim = args.amounttotrim
            else:
                amount_to_trim = 100
            __group_of_group_of_connections__.trim_flows(int(args.trimgroupid), amount_to_trim)
            __database__.root._p_changed = True

        # Subcomand to count the amount of models
        elif args.countconnections:
            try:
                filter = args.filter
            except AttributeError:
                pass
            __group_of_group_of_connections__.count_connections_in_group(args.countconnections, filter)
            __database__.root._p_changed = True

        # Subcomand to show the histograms 
        elif args.histogram:
            __group_of_group_of_connections__.show_histograms(args.histogram)

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
        group.add_argument('-n', '--editnote', metavar='dataset_id', help="Edit the note related with this dataset id.")
        group.add_argument('-N', '--delnote', metavar='dataset_id', help="Delete completely the note related with this dataset id.")
        group.add_argument('-o', '--editfolder', metavar='dataset_id', type=str, help="Edit the main folder of this dataset. Useful when you upload files from different machines and then you move them around.")

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
            __datasets__.delete(int(args.delete))
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

        # Subcomand to edit the note of this dataset
        elif args.editnote :
            __datasets__.edit_note(args.editnote)
            __database__.root._p_changed = True
            
        # Subcomand to delete the note of this dataset
        elif args.delnote :
            __datasets__.del_note(args.delnote)
            __database__.root._p_changed = True

        # Subcomand to edit the folder of this dataset
        elif args.editfolder :
            __datasets__.edit_folder(args.editfolder)
            __database__.root._p_changed = True
        else:
            parser.print_usage()


    ##
    # DATABASE
    #
    def cmd_database(self, *args):
        parser = argparse.ArgumentParser(prog="database", description="Manage the database", epilog="Manage database")
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-i', '--info', action="store_true", help="Info about the database connection")
        group.add_argument('-r', '--revert', action="store_true", help="Revert the connection of the database to the state before the last pack")
        group.add_argument('-p', '--pack', action="store_true", help="Pack the database")
        group.add_argument('-c', '--commit', action="store_true", help="Commit the changes")
        group.add_argument('-l', '--list', action="store_true", help="List the structures in the db.")
        group.add_argument('-d', '--delete', metavar="structurename", help="Delete the given structure from the db. Specify the complete name.")

        try:
            args = parser.parse_args(args)
        except:
            return

        # Subcomand to get info
        if args.info:
            __database__.info()

        # Subcomand to delete a structures
        elif args.delete:
            __database__.delete_structure(args.delete)

        # Subcomand to list the structures
        elif args.list:
            __database__.list_structures()

        # Subcomand to revert the database
        elif args.revert:
            __database__.revert()

        # Subcomand to pack he database
        elif args.pack:
            __database__.pack()

        # Subcomand to commit the changes
        elif args.commit:
            __database__.commit()


    ##
    # LABELS
    #
    # This command works with labels
    def cmd_labels(self, *args):
        parser = argparse.ArgumentParser(prog="labels", description="Manage labels", epilog="Manage labels")
        parser.add_argument('-l', '--list', action="store_true", help="List all existing labels.")
        parser.add_argument('-a', '--add', action="store_true", help="Add a label. Use -c to add to a connection_id (or IP) or -f to add to a group of connections id.")
        parser.add_argument('-c', '--connectionid', metavar="connection_id", help="Together with -a, add a label to the given connection_id or IP address. You should use -g to specify the id of the group of models.")
        parser.add_argument('-d', '--delete', metavar="label_id", help="Delete a label given the label number id. If you use a dash you can delete ranges of label ids. For example: -d 20-30")
        parser.add_argument('-F', '--deletefilter', action="store_true", help="Delete labels using the filter given with -f.")
        parser.add_argument('-D', '--deleteconnection', metavar="connection_id", help="Delete a label given a connection id to delete (4-tuple). You must give the group of model id with -g.")
        parser.add_argument('-g', '--modelgroupid', metavar="modelgroupid", help="Id of the group of models. Used with -a.")
        parser.add_argument('-m', '--migrate', action="store_true", help="Migrate <= 0.1.2alpha labels to the new database.")
        parser.add_argument('-f', '--filter', metavar="filter", nargs='+', default="", help="Use this filter to work with labels. Format: \"variable[!=<>]value\". You can use the variables: name, id, groupid and connid. Example: \"name=Botnet\". If you use -f to add labels, you should also specify -g. the variable connid is only used to assign a label to multiple connections")

        try:
            args = parser.parse_args(args)
        except:
            return

        # Subcomand to list labels
        if args.list:
            __group_of_labels__.list_labels(args.filter)

        # Subcomand to add a label
        elif args.add:
            if args.modelgroupid:
                # To a group of connections id using filters
                if args.filter:
                    __group_of_labels__.add_label_with_filter(args.modelgroupid, args.filter)
                # To a unique connections id
                elif args.connectionid:
                    __group_of_labels__.add_label(args.modelgroupid, args.connectionid)
            else:
                print_error('Please specify the id of the group of models where this connection belongs with -g.')

        # Subcomand to delete a label
        elif args.delete:
            __group_of_labels__.del_label(args.delete)
        # Subcomand to delete a label with filter
        elif args.deletefilter:
            if args.filter:
                __group_of_labels__.del_label(False, args.filter)
        # Subcomand to delete a specific connection
        elif args.deleteconnection:
            if args.modelgroupid:
                __group_of_labels__.delete_connection(args.modelgroupid, args.deleteconnection)
            else:
                print_error('You should give a group of models id with -g.')

        # Subcomand to migrate old labels
        elif args.migrate:
            __group_of_labels__.migrate_old_labels()


    ##
    # EXIT
    #
    def cmd_exit(self):
        # Exit is handled in other place. This is so it can appear in the autocompletion
        pass

