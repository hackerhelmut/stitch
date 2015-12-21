#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Implements DB functions to query service entries
"""
from stitch.datastore.utils import get_obj_defaultvalues, OBJT_SERVICE
def get_defaultvalues(service):
    """
    Returns the default values of a host
    """
    return get_obj_defaultvalues(OBJT_SERVICE, service)
