#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Simple python orchestration with fabric, yarn and fabtools
"""

import fabtools
from fabric import api
from host import deploy_services, deploy_users
import yarn

def options(parser):
    parser.add_argument('host')
    parser.add_argument('--login')
    parser.add_argument('--service')
    parser.add_argument('--user')

def execute(host, login=None, service=None, user=None, **unused_kw):
    """Updates a host from current database entries"""
    if not login:
        login = host
    if not service and not user:
        services = yarn.hosts.get_services(host).keys()
    with api.settings(host_string=login), fabtools.require.files.temporary_directory() as tmpdir:
        # Temp directory
        if service:
            deploy_services(host, [service], tmpdir)
        deploy_users(host, tmpdir)

