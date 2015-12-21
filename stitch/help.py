#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
stitch help <cmd>
  Shows extensive help of the command <cmd>.
"""

from fabric import state

def options(parser):
    """Options for the help command"""
    parser.add_argument('host')
    parser.add_argument('cmd')

def execute(cmd):
    """Show specific command"""
    state.commands.help(cmd)

