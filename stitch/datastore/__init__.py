#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Yarn main file see subfiles for more informations
"""
from . import environment
from stitch.datastore.environment import env, query
from . import yaml
from . import template

from . import hosts
from . import services
from . import users
from . import utils

def init(path='db'):
    """Initialize Yarn including env, template enigne and query engine"""
    environment.init(path)
    template.init()
