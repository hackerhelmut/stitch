#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Simple python orchestration with fabric, yarn and fabtools
"""
import os
from fabric import api
from fabtools import require
import fabtools
import yarn
from stitch.deploy.service import deploy_service_install, \
    deploy_service_files, deploy_service_script

def deploy_services(host, services = None, tmpdir = None):
    """The service update section of update_host"""
    for service in services:
        print "# Service {}".format(service)
        defaults = {
            "host": host,
            "service": service,
            "__dir__": os.path.join("db", "service", service),
            "__tmpdir__": tmpdir,
        }
        defaults.update(yarn.hosts.get_defaultvalues(host))
        defaults.update(yarn.utils.resolve(yarn.services.get_defaultvalues(service), **defaults))
        #defaults.update(yarn.services.get_defaultvalues(service))
        if api.env.debug:
            print defaults

        print "## Install"
        deploy_service_install(host, service, defaults)
        print "## Files"
        deploy_service_files(host, service, defaults)
        print "## Script"
        deploy_service_script(host, service, defaults)

def deploy_users(host, tempdir):
    """The user update section of update_host"""
    #check all useres of the host
    #for user in alluser:
    allgroups, allusers = yarn.hosts.get_system_groups_and_users(host)
    groups, users = yarn.hosts.get_groups_and_users(host)
    admgroups, admusers = yarn.hosts.get_groups_and_users(host, include_users=False)
    allusers += users
    allgroups += groups
    allusers = set(allusers)
    allgroups = set(allgroups)
    for group in groups:
        print "Require Group %s on %s" % (group, host)
        if not api.env.dryrun:
            require.groups.group(group)
        users.extend(yarn.users.get_users_of_group(group))
    for group in admgroups:
        admusers.extend(yarn.users.get_users_of_group(group))

    for user in users:
        defaults = {"host": host, "user": user}
        defaults.update(yarn.hosts.get_defaultvalues(host) or {})
        user_obj = yarn.users.by_name(user)
        #useraliases = yarn.utils.as_set(user_obj, "alias")
        #useraliases.add(user)
        #username = next(useralias
        #                for useralias in useraliases
        #                if fabtools.user.exists(useralias)) or user_obj["username"]
        print "Reqire User %s on %s" %(user, host)

        new_user = {
            "name": yarn.query("""$.user.'{user}'.username""", **defaults),
            "expiredate": yarn.query("""$.user.'{user}'.active and -1 or 1""", **defaults),
            "comment": yarn.query("""$.user.'{user}'.givenname+" "+$.user.'{user}'.suname""", **defaults),
            "home": None,
            "create_home": True,
            "skeleton_dir": yarn.query("""$host.'{host}'.skeleton_dir or null""", **defaults),
            "create_group": True,
            "extra_groups": yarn.query("""$.user.'{user}'.groups""", **defaults),
            "password": None,
            "system": False,
            "shell": "/bin/bash",
            "uid": None,
            "ssh_public_keys": yarn.query("""$.user.'{user}'.pubkeys.user.*""", **defaults),
            "non_unique": False,
        }
        if api.env.debug:
            print "New User:", new_user
        if not api.env.dryrun:
            require.user(**new_user)

    pubkeys = {}
    host_defaults = {"host": host}
    host_defaults.update(yarn.hosts.get_defaultvalues(host) or {})
    for user in admusers:
        defaults = dict(host_defaults)
        defaults["user"] = user
        pubkey = yarn.query("""$.user.'{user}'.pubkeys.admin.*""", **defaults)
        pubkeys.update(pubkey)

    if not api.env.dryrun:
        fabtools.user.add_ssh_public_keys('root', keys=pubkeys)

    if not api.env.dryrun:
        sysusers = set([user[0] for user in fabtools.user.list()])
        dangerous = sysusers - allusers
        if len(dangerous) > 0:
            print ("Warnung: Auf dem Host %s sind folgende Benutzer vorhanden, die nicht "+\
                "zugeordnet werden konnten:\n%s\n") % (host, ', '.join(dangerous))
    if not api.env.dryrun:
        sysgroups = set([group[0] for group in fabtools.group.list()])
        dangerous = sysgroups - allgroups
        if len(dangerous) > 0:
            print ("Warnung: Auf dem Host %s sind folgende Gruppen vorhanden, die nicht "+\
                "zugeordnet werden konnten:\n%s\n") % (host, ', '.join(dangerous))


