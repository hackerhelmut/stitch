#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Simple python orchestration with fabric and fabtools
"""

from operator import isMappingType
import os
import sys
import types
import argparse
from . import datastore
import fabric
import datetime

# For checking callables against the API, & easy mocking
from fabric import api, state, colors
from fabric.contrib import console, files, project

from fabric.network import disconnect_all, ssh
from fabric.state import env_options
from fabric.tasks import Task, execute, get_task_details
from fabric.task_utils import _Dict, crawl
from fabric.utils import abort, indent, warn, _pty_size
from .commands import Commands


def main():
    """
    Main command-line execution loop.
    """
    try:
        # Initialize Yarn Datastore
        datastore.init()
        # Register Python commands
        state.commands = Commands([
            'stitch.help',
            #'stitch.deploy',
            'stitch.query',
        ])
        # Register YAML commands
        state.commands.import_from_yaml()

        # Parse command line options
        parser = argparse.ArgumentParser(
            description='A python orchestration and deployment system.',
            #usage="%(prog)s [global_options] <CMD> [cmd_options] [cmd_params]"
        )
        parser.add_argument('-d', '--debug', action='store_true',
                            help='Switch on debug output')
        parser.add_argument('-D', '--dryrun', action='store_true',
                            help='Switch on dry run. Do not execute on remote host')
        state.commands.parse(parser)
        args = parser.parse_args()

        state.env.always_use_pty = True  # Disable use of remote ptys to prevent services hanging
        state.env.forward_agent = True   # Allow agent forwarding to enable sudo per ssh key
        state.env.use_ssh_config = True  # Read ssh config to allow special logins
        state.env.debug = args.debug     # Print debug messages
        state.env.dryrun = args.dryrun   # Print debug messages

        # Handle output control level show/hide
        #update_output_levels(show=options.show, hide=options.hide)
        arguments = dict(vars(args))
        del arguments['debug']
        del arguments['dryrun']
        del arguments['command']

        # Feed the env.tasks : tasks that are asked to be executed.
        state.env['tasks'] = [args.command]
        state.env['args'] = arguments
        state.env['__tmpdir__'] = "/tmp/stitch-{}".format(
            datetime.date.today().isoformat()
        )
        state.commands.execute(args.command)

        # If we got here, no errors occurred, so print a final note.
        if state.output.status:
            print "\n# Done."
    except SystemExit:
        # a number of internal functions might raise this one.
        raise

    except KeyboardInterrupt:
        if state.output.status:
            sys.stderr.write("\n# Stopped.\n")
        sys.exit(1)

    except fabric.exceptions.NetworkError as err:
        print "# Network Error", err
        sys.exit(1)

    except:
        sys.excepthook(*sys.exc_info())
        # we might leave stale threads if we don't explicitly exit()
        sys.exit(1)

    finally:
        disconnect_all()

    sys.exit(0)
