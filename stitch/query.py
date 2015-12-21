#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
stitch help <cmd>
  Shows extensive help of the command <cmd>.
"""

import stitch.datastore

def options(parser):
    """The query command has no options"""
    parser.add_argument('query')

def execute():
    """Show specific help for a command"""
    query = stitch.datastore.env.args.get("query")
    print "The Query \"\"\""+ query+ "\"\"\" returns:"
    res = stitch.datastore.query(query)
    print stitch.datastore.yaml.dump(res)

