# This file is part of the Stratosphere Testing Framework 
# See the file 'LICENSE' for copying permission.
# A large part of this file is taken from the Viper tool

import os
import glob
import atexit
import readline
import traceback

from stf.common.out import *
from stf.core.plugins import __modules__


version = "0.1.6alpha"

def logo():
    print("""
    Stratosphere Testing Framework
    https://stratosphereips.org
             _    __ 
            | |  / _|
         ___| |_| |_ 
        / __| __|  _|
        \__ \ |_| |  
    ... |___/\__|_|  ...
    """+version+"""

    """)



class Console(object):

    def __init__(self):
        # Create the nessesary folders first
        self.create_folders()

        # I have to move the import here.
        from stf.core.ui.commands import Commands

        # From some reason we should initialize the db from a method, we can not do it in the constructor
        from stf.core.database import __database__
        __database__.start()

        # This will keep the main loop active as long as it's set to True.
        self.active = True
        self.cmd = Commands()
        # Open the connection to the db. We need to make this here.
        self.db = __database__
        # When we exit, close the db
        atexit.register(self.db.close)
        self.prefix = ''

    def parse(self, data):
        root = ''
        args = []

        # Split words by white space.
        words = data.split()
        # First word is the root command.
        root = words[0]

        # If there are more words, populate the arguments list.
        if len(words) > 1:
            args = words[1:]

        return (root, args)


    def print_output(self, output, filename):
        if not output:
            return
        if filename:
            with open(filename.strip(), 'a') as out:
                for entry in output:
                    if entry['type'] == 'info':
                        out.write('[*] {0}\n'.format(entry['data']))
                    elif entry['type'] == 'item':
                        out.write('  [-] {0}\n'.format(entry['data']))
                    elif entry['type'] == 'warning':
                        out.write('[!] {0}\n'.format(entry['data']))
                    elif entry['type'] == 'error':
                        out.write('[!] {0}\n'.format(entry['data']))
                    elif entry['type'] == 'success':
                        out.write('[+] {0}\n'.format(entry['data']))
                    elif entry['type'] == 'table':
                        out.write(str(table(
                            header=entry['data']['header'],
                            rows=entry['data']['rows']
                        )))
                        out.write('\n')
                    else:
                        out.write('{0}\n'.format(entry['data']))
            print_success("Output written to {0}".format(filename))
        else:
            for entry in output:
                if entry['type'] == 'info':
                    print_info(entry['data'])
                elif entry['type'] == 'item':
                    print_item(entry['data'])
                elif entry['type'] == 'warning':
                    print_warning(entry['data'])
                elif entry['type'] == 'error':
                    print_error(entry['data'])
                elif entry['type'] == 'success':
                    print_success(entry['data'])
                elif entry['type'] == 'table':
                    print(table(
                        header=entry['data']['header'],
                        rows=entry['data']['rows']
                    ))
                else:
                    print(entry['data'])

    def stop(self):
        # Stop main loop.
        self.active = False
        # Close the db
        print_info('Wait until the database is synced...')
        self.db.close()                            

    def create_folders(self):
        """ Create the folders for the program"""
        # The name of the folder should read from the configuration file
        home_folder = '~/.stf/'
        stf_home_folder = os.path.expanduser(home_folder)

        # Create the ~/.stf/ folder for storing the history and the database
        if os.path.exists(stf_home_folder) == False:
            os.makedirs(stf_home_folder)

        # if there is an history file, read from it and load the history
        # so that they can be loaded in the shell.
        # just store it in the home directory.
        self.history_path = os.path.expanduser(stf_home_folder+'.stfhistory')

    def start(self):
        from stf.core.dataset import __datasets__
        # Logo.
        logo()
        self.db.list()

        # Setup shell auto-complete.
        def complete(text, state):
            # Try to autocomplete modules.
            mods = [i for i in __modules__ if i.startswith(text)]
            if state < len(mods):
                return mods[state]

            # Try to autocomplete commands.
            cmds = [i for i in self.cmd.commands if i.startswith(text)]
            if state < len(cmds):
                return cmds[state]

            # Then autocomplete paths.
            if text.startswith("~"):
                text = "{0}{1}".format(os.getenv("HOME"), text[1:])
            return (glob.glob(text+'*')+[None])[state]

        # Auto-complete on tabs.
        readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('set editing-mode vi')
        readline.set_completer(complete)


        # Save commands in history file.
        def save_history(path):
            readline.write_history_file(path)
        
        if os.path.exists(self.history_path):
            readline.read_history_file(self.history_path)

        # Register the save history at program's exit.
        atexit.register(save_history, path=self.history_path)

        # Main loop.
        while self.active:
            if __datasets__.current:
                self.prefix = red(__datasets__.current.get_name() + ': ')
            else:
                self.prefix = ''
            prompt = self.prefix + cyan('stf > ', True)

            # Wait for input from the user.
            try:
                data = raw_input(prompt).strip()
            except KeyboardInterrupt:
                print("")
            # Terminate on EOF.
            except EOFError:
                self.stop()
                print("")
                continue
            # Parse the input if the user provided any.
            else:
                # Skip if the input is empty.
                if not data:
                    continue

                # Check for output redirection
                filename = False

                # If there is a > in the string, we assume the user wants to output to file.
                # We erase this because it was interfering with our > filter
                #if '>' in data:
                #    temp = data.split('>')
                #    data = temp[0]
                #    filename = temp[1]
                
                # If the input starts with an exclamation mark, we treat the
                # input as a bash command and execute it.
                if data.startswith('!'):
                    os.system(data[1:])
                    continue

                # Try to split commands by ; so that you can sequence multiple
                # commands at once.
                split_commands = data.split(';')
                for split_command in split_commands:
                    split_command = split_command.strip()
                    if not split_command:
                        continue

                    # If it's an internal command, we parse the input and split it
                    # between root command and arguments.
                    root, args = self.parse(split_command)

                    # Check if the command instructs to terminate.
                    if root in ('exit', 'quit'):
                        self.stop()
                        continue

                    try:
                        # If the root command is part of the embedded commands list we
                        # execute it.
                        if root in self.cmd.commands:
                            self.cmd.commands[root]['obj'](*args)
                            
                        # If the root command is part of loaded modules, we initialize
                        # the module and execute it.
                        elif root in __modules__:
                            module = __modules__[root]['obj']()
                            module.set_commandline(args)
                            module.run()

                            self.print_output(module.output, filename)
                            del(module.output[:])
                        else:
                            print("Command not recognized.")
                    except KeyboardInterrupt:
                        pass
                    except Exception as e:
                        print_error("The command {0} raised an exception:".format(bold(root)))
                        traceback.print_exc()

