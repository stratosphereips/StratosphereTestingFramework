# This file is part of Viper - https://github.com/botherder/viper
# See the file 'LICENSE' for copying permission.

import argparse


class Module(object):
    cmd = ''
    description = ''
    command_line = []
    args = None
    authors = []
    output = []

    def __init__(self):
        self.parser = ArgumentParser(prog=self.cmd, description=self.description)

    def set_commandline(self, command):
        self.command_line = command

    def log(self, event_type, event_data):
        self.output.append(dict(
            type=event_type,
            data=event_data
        ))

    def usage(self):
        self.log('', self.parser.format_usage())

    def help(self):
        self.log('', self.parser.format_help())

    def run(self):
        try:
            self.args = self.parser.parse_args(self.command_line)
        except ArgumentErrorCallback as e:
            self.log(*e.get())
