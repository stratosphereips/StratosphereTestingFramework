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
from stf.core.experiment import __experiments__
from stf.core.dataset import __datasets__
from stf.core.database import __database__

class Commands(object):

    def __init__(self):
        # Open connection to the database.
        # Map commands to their related functions.
        self.commands = dict(
            help=dict(obj=self.cmd_help, description="Show this help message"),
            info=dict(obj=self.cmd_info, description="Show information on the opened experiment"),
            clear=dict(obj=self.cmd_clear, description="Clear the console"),
            experiments=dict(obj=self.cmd_experiments, description="List or switch to existing experiments"),
            datasets=dict(obj=self.cmd_datasets, description="Manage the datasets"),
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
    # DATASETS
    #
    # This command works with datasets
    def cmd_datasets(self, *args):
        parser = argparse.ArgumentParser(prog="datasets", description="Manage datasets", epilog="Manage datasets")
        #group = parser.add_mutually_exclusive_group()
        parser.add_argument('-l', '--list', action="store_true", help="List all existing datasets")
        parser.add_argument('-c', '--create', metavar='dataset_filename', help="Create a new dataset from a file")
        parser.add_argument('-d', '--delete', metavar='dataset_id', help="Delete a dataset")
        parser.add_argument('-f', '--list_files', metavar='dataset_id', help="List all the files in a given dataset")
        parser.add_argument('-i', '--info', metavar='dataset_id', help="Give more info about a file in a dataset. Put the dataset id here and the file id with the -F option.")
        parser.add_argument('-F', '--file', metavar='file_id', help="File id to give more info about. Used with -i option")

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

        # Subcomand to list files
        elif args.list_files:
            __datasets__.list_files(args.list_files)

        # Subcomand to get info about a file in a dataset
        elif args.info and args.file :
            __datasets__.info_about_file(args.info, args.file)

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

