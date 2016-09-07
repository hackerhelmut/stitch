#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Simple python orchestration with fabric, stitch.datastore and fabtools
"""
from __future__ import print_function
import os
from .datastore.utils import resolve
from .datastore.hosts import get_file_iterator
from .datastore.template import Template
from .datastore.environment import env
from fabric import api
from pipes import quote

class Directory(object):
    """Directory Guard"""
    def __init__(self, defaults):
        """Create Directory from defaults"""
        super(Directory, self).__init__()
        self.path = defaults.get("__tmpdir__")
        self.host = defaults.get("host", "localhost")

    def __enter__(self):
        """Create directory"""
        if env.dryrun:
            print("### Host: %s" % self.host, '#' * (100-len("### Host: %s " % self.host)))
            print("mkdir -p %s" % quote(self.path))
        elif self.path == 'localhost':
            api.local("mkdir -p %s" % quote(self.path))
        else:
            api.run('mkdir -p %s' % quote(self.path))
        return self

    def __exit__(self, typeclass, value, traceback):
        """Destroy directory"""
        if env.dryrun:
            print("# Host: %s" % self.host)
            print("rm -rf %s" % quote(self.path))
        elif self.path == 'localhost':
            api.local("rm -rf %s" % quote(self.path))
        else:
            api.sudo('rm -rf %s' % quote(self.path))

def render_template(template, defaults):
    """Render script template to string"""
    if not isinstance(template, Template):
        filename = template.format(**defaults)
        template = Template(filename=filename)
    return template.format(**defaults)

def execute_scripts(obj, defaults):
    """Execute a template script"""
    from StringIO import StringIO
    if "execute" in obj:
        scriptname = obj.get("execute")
        script = render_template(scriptname, defaults)
        if defaults.get("dryrun", False):
            print(script.encode('utf8'))
        else:
            filehandler = StringIO()
            filehandler.write(script)
            remote_script = os.path.join(
                defaults.get("__tmpdir__"),
                "{}-script.sh".format(defaults.get("host", "localhost"))
            )

            api.put(
                local_path=filehandler,
                remote_path=remote_script,
                mode='0555',
                use_sudo=True,
                temp_dir=defaults.get("__tmpdir__")
            )
            api.sudo(remote_script)

def execute_store(obj, defaults):
    """Download files from the system"""
    for fileobj in obj.get("store", []):
        for store, store_defaults in get_file_iterator(fileobj, defaults):
            source = store.get("path").format(**store_defaults)
            destination = store.get("destination").format(**store_defaults)
            destdir = os.path.dirname(destination)

            if defaults.get("dryrun", False):
                print("# Create dir '%s'" % destdir)
                print("# Retrive {} to {}".format(source, destination))
            else:
                api.local("mkdir -p '%s' || true" % destdir)
                api.get(source, destination, use_sudo=True)

def execute_step(obj, defaults):
    """Execute step rule"""
    for step_obj in obj.get("steps", []):
        hosts = []
        if "hosts" in step_obj:
            hosts = resolve(step_obj["hosts"], **defaults)
            if isinstance(hosts, str):
                hosts = hosts.replace(",", " ").split(" ")
            if "exclude" in env.args:
                exclude = env.args["exclude"].split(',')
                hosts = [host for host in hosts if host not in exclude]
        if any(hosts):
            for host in hosts:
                step_defaults = dict(defaults)
                step_defaults["host"] = host
                with api.settings(host_string=host):
                    with Directory(step_defaults):
                        step_defaults.update(
                            **resolve(step_obj.get('defaults', {}), **step_defaults))

                        execute_scripts(step_obj, step_defaults)
                        execute_store(step_obj, step_defaults)
        else:
            with Directory(defaults):
                step_defaults = dict(defaults)
                step_defaults.update(**resolve(step_obj.get('defaults', {}), **step_defaults))

                execute_scripts(step_obj, step_defaults)
                execute_store(step_obj, step_defaults)

