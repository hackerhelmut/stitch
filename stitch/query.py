#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
stitch help <cmd>
  Shows extensive help of the command <cmd>.
"""

from fabric import state
import yarn

def options(parser):
    parser.add_argument('query')

def execute(query, **unused_kw):
    """Show specific help for a command"""
    print "The Query \"\"\""+ query+ "\"\"\" returns:"
    res = yarn.query(query)
    print yarn.yaml.dump(res)

