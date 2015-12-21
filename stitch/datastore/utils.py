#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Implements common functions
"""
import types
import itertools
from stitch.datastore.environment import query, env
from stitch.datastore.template import Template
from stitch.datastore import yaml
from ruamel.yaml.comments import CommentedMap
import sys

OBJT_USER = "user"
OBJT_HOST = "host"
OBJT_SERVICE = "service"

def resolve(obj, **defaults):
    """Takes a dict sructure and resolves all queries"""
    try:
        result = None
        if isinstance(obj, yaml.Query):
            result = query(obj.query, **defaults)
        elif isinstance(obj, list):
            result = []
            for item in obj:
                result.append(resolve(item, **defaults))
        elif isinstance(obj, dict):
            result = {}
            for key, item in obj.items():
                    result[key] = resolve(item, **defaults)
        elif isinstance(obj, Template):
            result = obj.format(**defaults)
        elif isinstance(obj, (str, unicode)):
            result = obj.format(**defaults)
        else:
            result = obj
        return result
    except KeyError as err:
        print "################################################################"
        print "The Key {} was not found in the dict. The following keys are available:".format(err.message)
        print ", ".join(defaults.keys())
        print ""
        print "For more information run in debug mode (-d)"
        if env.debug:
            import traceback
            traceback.print_stack()
            traceback.print_exc()
        sys.exit(1)
env['template']['functions']['resolve_queries'] = resolve

def shasum(text):
    import hashlib
    m = hashlib.sha1()
    m.update(text)
    return m.hexdigest()
env['template']['filters']['shasum'] = shasum

def base64(text):
    import base64
    return base64.b64encode(text)
env['template']['filters']['base64'] = base64

def as_list(obj, attrs):
    """
        Returns the value of an attribute of an object.
        The result will always be in a list.
    """
    if isinstance(attrs, list):
        for attr in attrs:
            value = obj.get(attr, None)
            if value:
                break
    else:
        value = obj.get(attr, None)
    if not value:
        value = []
    if not isinstance(value, list):
        value = [value]
    return value

def as_set(obj, attr):
    """
        Returns the value of an attribute of an object.
        The result will always be in a list.
    """
    return set(as_list(obj, attr))


def get_obj_default(objtype):
    """
        Get default object for a specific object type
        objtype can be one of host, user, service
    """
    default = query("$.default.'{objtype}'", objtype=objtype)
    obj = CommentedMap(default, relax=True)
    del obj[yaml.FILE_PROPERTY]
    return obj

def get_obj_defaultvalues(objtype, name):
    """
        Get default values for a specific object
        objtype can be one of host, user, service
        name must be the name of the object
    """
    result = query("$.'{objtype}'.'{"+objtype+"}'.defaults", **{"objtype":objtype, objtype:name})
    if not result:
        result = {}
    result[objtype] = name
    return result

def get_obj_by_name(objtype, name, create_obj=True):
    """
        Returns a single object dict by its name or alias.
        Valid object types are OBJT_USER, OBJT_HOST.
        If create_obj is True (default) a new user will be
        derived from the default user template.
    """
    obj = query("$.'{type}'..*[('{name}' in @.'{type}name' or '{name}' in @.alias) and @]",
                type=objtype, name=name)
    if isinstance(obj, (types.GeneratorType, itertools.chain)):
        obj = list(obj)
        if not len(obj) == 0:
            obj = obj[0]
        else:
            obj = None
    if not obj and create_obj:
        obj = get_obj_default(objtype)
    return obj
