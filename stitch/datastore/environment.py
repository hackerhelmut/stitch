#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Implements direct environment in memory DB for Yarn
"""
import os
import os.path
import types
import itertools
from objectpath import Tree
from fabric.api import env
from stitch.datastore import yaml

env["datastore"] = {}
env["template"] = {
    'filters': {},
    'functions': {},
}

def loaddir(path):
    """Load yaml files from a directory"""
    dict_object = {}
    for itemname in os.listdir(path):
        if itemname in ['.git']:
            continue
        item_obj = {}
        item_dir = os.path.join(path, itemname)
        item_file = os.path.join(path, itemname)
        if os.path.isdir(item_dir):
            item_obj = loaddir(item_dir)
            dict_object[itemname] = item_obj
        if os.path.isfile(item_file) and item_file.endswith(yaml.FILE_EXTENSION):
            item_obj = yaml.load(item_file)
            name = itemname[:-5]
            if hasattr(item_obj, "get"):
                name = item_obj.get("name", itemname[:-5])
            dict_object[name] = item_obj
    return dict_object

def load(path='db'):
    """Recursivly load a db directory"""
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    env["datastore"].update({
        "type": "yamldir",
        "path": path,
    })
    return loaddir(path)

def init(path='db'):
    """Initialize a stitch.datastore db"""
    env.conf = load(path)
    env['debug'] = False

def query(querystr, **kw):
    """Query the current database with ObjectPath"""
    def query_getter(obj, attr):
        """Extended object getter to allow lazy recursive query resolving"""
        if isinstance(obj, types.GeneratorType):
            obj = tuple(obj)
        elif isinstance(obj, itertools.chain):
            obj = list(obj)
        if isinstance(obj, yaml.Query):
            res = query(obj.query, **kw)
            if attr:
                return res.get(attr)
            else:
                return res
        elif isinstance(obj, yaml.CommentedMap):
            res = obj.get(attr)
        try:
            if attr:
                return obj.__getattribute__(attr)
            else:
                return obj
        except AttributeError:
            return obj
    def first_funct(*k):
        """Returns the first result"""
        if len(k) == 1 and isinstance(k[0], (tuple, list)):
            k = k[0]
        for obj in k:
            if isinstance(obj, types.GeneratorType):
                obj = tuple(obj)
                if len(obj) == 1:
                    obj = obj[0]
                elif not len(obj):
                    obj = None
            elif isinstance(obj, itertools.chain):
                obj = list(obj)
                if len(obj) == 1:
                    obj = obj[0]
                elif not len(obj):
                    obj = None
            if obj != None:
                return obj
        return None
    def update_funct(*k):
        """Allow dict.update in a query"""
        result = {}
        if isinstance(result, dict):
            for extra in k:
                if isinstance(extra, dict):
                    result.update(extra)
        return result
    def keys_funct(dictionary):
        """Allow dict.keys in a query"""
        if isinstance(dictionary, dict):
            return dictionary.keys()
        return dictionary
    def values_funct(dictionary):
        """Allow dict.values in a query"""
        if isinstance(dictionary, dict):
            return dictionary.values()
        return dictionary
    def host_funct(hostname=None):
        if isinstance(hostname, dict):
            result = dict()
            for key, host in hostname.items():
                result[key] = host_funct(host)
            return result
        elif isinstance(hostname, (list, tuple)):
            result = list()
            for host in hostname:
                result.append(host_funct(host))
            return result
        else:
            newkw = dict(kw)
            if hostname:
                newkw['host'] = hostname
            return query("$.host.'{host}'", **newkw)
    def service_funct(servicename=None):
        if isinstance(servicename, dict):
            result = dict()
            for key, service in servicename.items():
                result[key] = service_funct(service)
            return result
        elif isinstance(servicename, (list, tuple)):
            result = list()
            for service in servicename:
                result.append(service_funct(service))
            return result
        else:
            newkw = dict(kw)
            if servicename:
                newkw['service'] = servicename
            return query("$.service.'{service}'", **newkw)

    tree = Tree(env.conf, cfg={
        "debug": False,
        "object_getter": query_getter
    })
    tree.register_function("first", first_funct)
    tree.register_function("update", update_funct)
    tree.register_function("keys", keys_funct)
    tree.register_function("values", values_funct)
    tree.register_function("host", host_funct)
    tree.register_function("service", host_funct)

    full_query = querystr.format(**kw)
    if env.debug:
        print querystr, full_query
    res = tree.execute(full_query)
    if env.debug:
        print full_query, res
    return query_getter(res, None)
