#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Implements DB functions to query host entries
"""
from __future__ import print_function
import collections
from stitch.datastore.environment import query, env, deepcopy
from stitch.datastore.utils import get_obj_by_name, get_obj_defaultvalues, OBJT_HOST
from stitch.datastore.utils import resolve

def get_system_groups_and_users(host):
    """Returns system groups and users"""
    users = query("$.host.'{host}'.pam", host=host) or []
    if isinstance(users, (str, unicode)):
        users = users.replace(', ', ' ').replace(',', ' ').split(' ')
    groups = [group[1:] for group in users if group and group.startswith("+")]
    both = [group[1:] for group in users if group and group.startswith("=")]
    users = [user for user in users if group and not user.startswith("+") and not user.startswith("=")]
    return list(groups + both), list(users + both)

def get_user_list(host):
    """Creates a list of uesrs allowd to login the host"""
    users = query("$.host.'{host}'.user", host=host)
    if isinstance(users, (str, unicode)):
        users = users.replace(', ', ' ').replace(',', ' ').split(' ')
    return users or []

def get_admin_list(host):
    """Creates a list of user allowed to administrate the host"""
    users = query("$.host.'{host}'.admin", host=host)
    if isinstance(users, (str, unicode)):
        users = users.replace(', ', ' ').replace(',', ' ').split(' ')
    return users or []

def get_groups_and_users(host, include_users=True, include_admins=True):
    """Returns a list of useres allowed on the host"""
    users = get_user_list(host) if include_users else []
    admins = get_admin_list(host) if include_admins else []
    groups = [group[1:] for group in users + admins if group and group.startswith("+")]
    both = [group[1:] for group in users + admins if group and group.startswith("=")]
    users = [user for user in users + admins if group and not user.startswith("+") and not user.startswith("=")]
    return list(groups + both), list(users + both)
env['template']['functions']['get_host_groups_and_users'] = get_groups_and_users

def resolve_users(host, only_admins=True):
    from stitch.datastore import users
    grouplist, userlist = get_groups_and_users(host, not only_admins)
    userset = set(userlist)
    for group in grouplist:
        for user in users.get_users_of_group(group):
            userset.add(user)
    return list(userset)
env['template']['functions']['resolve_host_users'] = resolve_users

def get_file_iterator(file_object, service_defaults):
    file_defaults = {}
    file_defaults.update(service_defaults)

    iterator = file_object.get('iter', [''])
    if isinstance(iterator, dict):
        file_defaults["iter"] = {}
        def iter_dict(iterator, keys, file_obj, defaults):
            """Helper function to recursivly go through all nested iterator combinations"""
            result = []
            if len(keys):
                name = keys[0]
                rest = keys[1:]
                for item in resolve(iterator[name], **defaults):
                    defaults['iter'][name] = item
                    result += iter_dict(iterator, rest, file_obj, deepcopy(defaults))
            else:
                final_defaults = defaults
                final_defaults.update(resolve(file_obj.get('defaults', {}), **defaults))
                return [(file_obj, final_defaults)]
            return result

        return iter_dict(iterator, iterator.keys(), file_object, file_defaults)
    else:
        result = []
        iterator = resolve(file_object.get('iter', ['']), **file_defaults)
        if not isinstance(iterator, collections.Iterable):
            import sys
            print("Error: The iterator 'iter' of the path '{}' of service '{}' in host '{}' is not iterable".format(file_object.get('path', file_object.get('dst', "<unknown>")), service_defaults['service'], service_defaults['host']))
            sys.exit(1)

        for item in iterator:
            file_defaults["iter"] = item
            file_defaults.update(resolve(file_object.get('defaults', {}), **file_defaults))
            result += [(file_object, deepcopy(file_defaults))]
        return result
env['template']['functions']['service_get_file_iterator'] = get_file_iterator

def import_file(filename, default=None):
    try:
        with open(filename, 'r') as filehandle:
            return filehandle.read().decode('utf8')
    except IOError:
        return default
env['template']['functions']['import_file'] = import_file

def get_services(host):
    """Returns a list of services on the host"""
    services = query("$.host.'{host}'.service", host=host)
    return services

def by_name(name, create_user=True):
    """
        Returns a single host dict by its hostname or alias.
        If create_host is True (default) a new user will be
        derived from the default user template.
    """
    return get_obj_by_name(OBJT_HOST, name, create_user)

def get_defaultvalues(host):
    """
    Returns the default values of a host
    """
    return get_obj_defaultvalues(OBJT_HOST, host)
