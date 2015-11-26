#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Simple python orchestration with fabric, yarn and fabtools
"""

from operator import isMappingType
import os
import sys
import types
import argparse
import yarn
import fabric

# For checking callables against the API, & easy mocking
from fabric import api, state, colors
from fabric.contrib import console, files, project

from fabric.network import disconnect_all, ssh
from fabric.state import env_options
from fabric.tasks import Task, execute, get_task_details
from fabric.task_utils import _Dict, crawl
from fabric.utils import abort, indent, warn, _pty_size
from stitch.utils import Commands

def query(querystr, *args, **kw):
    """Query yarn db manually"""
    print querystr, args
    for arg in args:
        (key, val) = arg.split('=')
        kw[key] = val
    res = yarn.query(querystr, **kw)
    print yarn.yaml.dump(res)

def main():
    """
    Main command-line execution loop.
    """
    try:
        state.commands = Commands([
            'stitch.help',
            'stitch.deploy',
            'stitch.virsh',
            'stitch.query',
        ])
        yarn.init()

        # Parse command line options
        parser = argparse.ArgumentParser(
            description='A python orchestration and deployment system.',
            usage="%(prog)s [global_options] <CMD> [cmd_options] [cmd_params]"
        )

        parser.add_argument('-d', '--debug', action='store_true',
            help='Switch on debug output'
        )
        parser.add_argument('-D', '--dryrun', action='store_true',
            help='Switch on dry run. Do not execute on remote host'
        )

        state.commands.parse(parser)
        args = parser.parse_args()

        state.env.always_use_pty = True  # Disable the use of remote ptys to prevent services hanging
        state.env.forward_agent = True   # Allow agent forwarding to enable sudo per ssh key
        state.env.use_ssh_config = True  # Read ssh config to allow special logins
        state.env.debug = args.debug     # Print debug messages
        state.env.dryrun = args.dryrun   # Print debug messages
        # Update env with any overridden option values
        # NOTE: This needs to remain the first thing that occurs
        # post-parsing, since so many things hinge on the values in env.
        """
        for option in env_options:
            state.env[option.dest] = getattr(options, option.dest)
        """
        # Handle output control level show/hide
        #update_output_levels(show=options.show, hide=options.hide)
        kw = dict(vars(args))
        del kw['debug']
        del kw['command']
        # Feed the env.tasks : tasks that are asked to be executed.
        state.env['tasks'] = [args.command]
        state.commands[args.command][2](**kw)
        #execute(args.command, **kw)

        # If we got here, no errors occurred, so print a final note.
        if state.output.status:
            print("\nDone.")
    except SystemExit:
        # a number of internal functions might raise this one.
        raise
    except KeyboardInterrupt:
        if state.output.status:
            sys.stderr.write("\nStopped.\n")
        sys.exit(1)
    except fabric.exceptions.NetworkError as err:
        print "Network Error", err
        sys.exit(1)
    except:
        sys.excepthook(*sys.exc_info())
        # we might leave stale threads if we don't explicitly exit()
        sys.exit(1)
    finally:
        disconnect_all()
    sys.exit(0)
    """
        # Shortlist is now just an alias for the "short" list format;
        # it overrides use of --list-format if somebody were to specify both
        if options.shortlist:
            options.list_format = 'short'
            options.list_commands = True

        # If user didn't specify any commands to run, show help
        if not (arguments or remainder_arguments or default):
            parser.print_help()
            sys.exit(0)  # Or should it exit with error (1)?
        """
