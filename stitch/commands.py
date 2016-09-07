#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Simple python orchestration with fabric, stitch.datastore and fabtools
"""
from __future__ import print_function
import stitch.datastore
from stitch.datastore.utils import resolve
from stitch.execution import execute_step

class Commands(dict):
    """A simple dict extension to store command tuples"""
    def __init__(self, lst):
        """
        With in the constructor a list of python modules names is given.
        The module must contain the typical stitch command structure.
        Which means the docstring of the module, option and execute method
        as well as the docstring of the execution method are important.

        In the options method the subparser for the arguments of the commands
        is filled.
        Execute is executed with all argeuments in the kw args.
        """
        super(Commands, self).__init__()

        import importlib
        for cmd in lst:
            mod = importlib.import_module(cmd)
            name = getattr(mod, '__name__', cmd).split('.')[-1]
            doc = getattr(mod, '__doc__', "")
            options = getattr(mod, 'options', None)
            funct = getattr(mod, 'execute', None)
            if funct:
                self[name] = (doc, options, funct)

    def add_yaml_command(self, cmd):
        """Create and register YAML command"""
        name = cmd.get("name")
        doc = cmd.get("help", "")
        description = cmd.get("description", "")
        args = cmd.get("arguments", {})
        obj = dict(cmd)
        def options(parser):
            """Get options from yaml file"""
            for k, kwargs in args.items():
                if not kwargs:
                    kwargs = {}
                parser.add_argument(*k, **kwargs)
        def execute():
            """Execute YAML description"""
            global_defaults = dict(stitch.datastore.env)
            global_defaults.update(**resolve(obj.get("defaults", {}), **global_defaults))
            execute_step(obj, global_defaults)
        execute.__doc__ = description
        self.add_command(name, doc, options, execute)

    def import_from_yaml(self):
        """Import all commands from the stitch.datastore datastore"""
        for cmd in stitch.datastore.env.conf.get("command", {}).values():
            self.add_yaml_command(cmd)

    def add_command(self, name, doc, options, funct):
        """Adding firther commands"""
        self[name] = (doc, options, funct)

    def help(self, name):
        """Show help of the command with the name name"""
        if name in self:
            print(self[name][0])

    def execute(self, name):
        """Execute the command with name name and all the arguments in the kw dict"""
        return self[name][2]()

    def parse(self, parser):
        """Create argparser for all subcommands"""
        commands = parser.add_subparsers(
            title='Available Command',
            help="Available commands",
            dest='command'
        )
        for key, cmd in self.items():
            subparser = commands.add_parser(key, help=cmd[2].__doc__)
            if cmd[1]:
                cmd[1](subparser)
        return commands
