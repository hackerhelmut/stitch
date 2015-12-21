#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Implements DB functions to query user entries
"""
from stitch.datastore.environment import query
from stitch.datastore.utils import get_obj_by_name, OBJT_USER

def get_users_of_group(name):
    """
    Returns all users listing to be member in a specific group
    """
    if name.startswith('+') or name.startswith('='):
        name = name[1:]
    users = query("$.user..*[('{group}' in @.groups or '{group}' in @.group) and @].username", group=name)
    if not users:
        users = []
    elif not isinstance(users, list):
        users = list(users)
    return users

def by_name(name, create_user=True):
    """
        Returns a single user dict by its username or alias.
        If create_user is True (default) a new user will be
        derived from the default user template.
    """
    return get_obj_by_name(OBJT_USER, name, create_user)

