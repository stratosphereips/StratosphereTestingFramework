# This file is part of the Stratosphere Testing Framework 
# See the file 'LICENSE' for copying permission.
# Most of this file is copied from Viper

import argparse
import os
import time
import fnmatch
import tempfile
import shutil

from stf.common.out import *
from stf.core.experiment import __experiments__
#from stf.core.plugins import __modules__
from stf.core.database import Database

class Commands(object):

    def __init__(self):
        # Open connection to the database.
        # Map commands to their related functions.
        self.commands = dict(
            help=dict(obj=self.cmd_help, description="Show this help message"),
            info=dict(obj=self.cmd_info, description="Show information on the opened experiment"),
            clear=dict(obj=self.cmd_clear, description="Clear the console"),
            experiments=dict(obj=self.cmd_experiments, description="List or switch to existing experiments"),
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

        rows.append(["exit, quit", "Exit Viper"])
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
        if __experiments__.is_set():
            print(table(
                ['Key', 'Value'],
                [
                    ('Name', __experiments__.current.file.name),
                ]
            ))



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

        try:
            args = parser.parse_args(args)
        except:
            return

        if args.list:
            print_info("Experiments Available:")

            rows = []
            for experiment in __experiments__.list_all():
                    rows.append([experiment.get_name(), experiment.get_id() , experiment.get_ctime(), __experiments__.is_current(experiment.get_id())])

            print(table(header=['Experiment Name', 'Id', 'Creation Time', 'Current'], rows=rows))

        elif args.switch:
            __experiments__.switch_to(args.switch)
            print_info("Switched to experiment {0}".format(bold(args.switch)))

        elif args.create:
            __experiments__.create(args.create)
            print_info("Created experiment {0}".format(bold(args.create)))

        else:
            parser.print_usage()

