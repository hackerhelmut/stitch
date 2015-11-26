#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Simple python orchestration with fabric, yarn and fabtools
"""
from fabric import api
from fabtools import require
import collections
import fabtools
import yarn
import sys
import os

def deploy_service_install(host, service, defaults):
    """Install packages of a service on a specific host"""
    # Install Packages
    ## Debian Family
    if yarn.query("$.host.'{host}'.defaults.os.family", **defaults) == "debian":
        install = yarn.query("$.service.'{service}'.install.'{os[distribution]}-{os[release]}'"+\
                " or $.service.'{service}'.install.'{os[distribution]}'", **defaults)
        if isinstance(install, dict):
            for keyserver, keys in install.get("keys", {}).items():
                for key in keys:
                    if not api.env.dryrun:
                        require.deb.key(key, keyserver=keyserver)
                    else:
                        print "Key {} from {} must be installed".format(key, keyserver)
            for source in yarn.utils.as_list(install, ['sources', 'source']):
                if isinstance(source, str):
                    uri = source
                else:
                    uri = source.get("uri", None)
                if uri:
                    if uri.startswith("ppa:"):
                        if not api.env.dryrun:
                            require.deb.ppa(uri)
                        else:
                            print "PPA {} must be installed".format(uri)
                    else:
                        name = source.get("name", None)
                        distribution = source.get("distribution", None)
                        components = yarn.utils.resolve(yarn.utils.as_list(source, [
                            'components', 'component']), **defaults)
                        if not name or not distribution or not components:
                            print "Error: To define a debian family package you must either"+\
                                    " give a ppa uri or a name, uri, distribution and component"
                        if not api.env.dryrun:
                            require.deb.source(name, uri, distribution, *components)
                        else:
                            print "{}: deb {} {} {}".format(name, uri, distribution, ' '.join(components))
                else:
                    print "Error: Service install statement not complete for service '%s'" % (
                        service)
            packages = yarn.utils.resolve(yarn.utils.as_list(install, [
                'packages', 'package']), **defaults)
            if any(packages):
                if not api.env.dryrun:
                    require.deb.packages(packages)
                else:
                    print "Packages will be installed: {}".format(' '.join(packages))
        elif install != None:
            print "Error"
    ## Archlinux
    ## OpenWRT

def deploy_service_files_file(host, service, file_obj, file_defaults):
    """Check a file on the target host and create it when needed"""
    fstype = yarn.utils.resolve(
        file_obj.get('type', 'file'), **file_defaults)
    source = yarn.utils.resolve(
        file_obj.get('src', file_obj.get('source', None)), **file_defaults)
    url = yarn.utils.resolve(
        file_obj.get('url', None), **file_defaults)
    destination = yarn.utils.resolve(
        file_obj.get('dst', file_obj.get('path', None)), **file_defaults)
    contents = yarn.utils.resolve(file_obj.get('content', file_obj.get(
        'contents', None)), **file_defaults)
    options = {
        'use_sudo': True,
        'owner': None,
        'group': '',
        'mode': None,
    }
    if not fstype in ['dir', 'symlink']:
        options.update({
            'md5': None,
            'verify_remote': True,
            'temp_dir': '/tmp',
        })
    if source and not isinstance(source, str):
        print "%s: %s: Source file must be string!" % (host, service)
        sys.exit(1)
    if destination and not isinstance(destination, str):
        print "%s: %s: Path must be string!" % (host, service)
        sys.exit(1)
    if contents and not isinstance(contents, yarn.yaml.Template):
        print "%s: %s: Contents must be a template!" % (host, service)
        sys.exit(1)

    options.update(file_obj.get('options', {}))
    options = yarn.utils.resolve(options, **file_defaults)
    if fstype == 'dir':
        if not api.env.dryrun:
            fabtools.require.files.directory(destination, **options)
        else:
            print "Directory {} must exists with options {}".format(destination, options)
    elif fstype == 'symlink':
        use_sudo = options['use_sudo']
        funct = api.sudo if use_sudo else api.run
        if not api.env.dryrun:
            if fabtools.files.exists(destination, use_sudo) and \
               funct('readlink -f %(path)s' % {"path": destination}) != source:
                fabtools.files.remove(destination, use_sudo)
            fabtools.files.symlink(source, destination, use_sudo)
        else:
            print "Symlink {} must exist to target {}".format(destination, source)
    else:
        ## Templates
        if api.env.debug:
            print destination, file_defaults
        if source and isinstance(source, str) and source.endswith('.j2') or (contents and \
                isinstance(contents, yarn.yaml.Template)):
            from jinja2 import Template
            from jinja2.exceptions import TemplateSyntaxError
            if source:
                template = yarn.yaml.Template(filename=source)
                contents = template.format(file_defaults)
                source = None
            elif contents:
                contents = contents.format(file_defaults)

        if "generate" in file_obj:
            generate = yarn.utils.resolve(file_obj["generate"], **file_defaults)
            execute = generate.get('execute', None) if isinstance(generate, dict) else generate
            save = generate.get('save', None) if isinstance(generate, dict) else None
            obj = generate.get('object', [None])[0] if isinstance(generate, dict) else None
            attr = generate.get('attr', None) if isinstance(generate, dict) else None
            if not save or not obj or not attr:
                print "Error you need to provide save, object and attr"

            contents = obj.get(attr, None) if obj and attr else None
            if api.env.dryrun:
                print "File {} will be generated by '{}'".format(destination, execute.format(file_defaults))
            elif not execute:
                print "No execute statement"
            else:
                if not fabtools.files.exists(destination, use_sudo=options['use_sudo']):
                    print "file does not exist:", destination
                    use_sudo = options['use_sudo']
                    funct = api.sudo if use_sudo else api.run
                    funct(execute.format(file_defaults))
                    if save and obj and attr:
                        store = funct("cat %s" % destination)
                        store = yarn.yaml.literal_str(store)
                        obj[attr] = store
                        yarn.yaml.save(save)
                elif contents:
                    require.files.file(destination, contents, **options)


        else:
            if api.env.dryrun:
                print "### File {} will be '{}', '{}' or '{}'".format(destination, source, url, contents)
            else:
                require.files.file(destination, contents, source, url, **options)


def deploy_service_files(host, service, defaults):
    """Copy over configuration files of a ceartain service"""
    # Copy files
    for file_obj in yarn.query("$.service.'{service}'.fs", **defaults) or []:
        file_defaults = {}
        file_defaults.update(defaults)
        defaults["iter"] = {}

        iterator = file_obj.get('iter', [''])
        if isinstance(iterator, dict):
            def iter_dict(iterator, keys, file_obj, defaults):
                """Helper function to recursivly go through all nested iterator combinations"""
                if len(keys):
                    name = keys[0]
                    rest = keys[1:]
                    if api.env.debug:
                        print name, rest, iterator[name]
                    for item in yarn.utils.resolve(iterator[name], **defaults):
                        defaults['iter'][name] = item
                        iter_dict(iterator, rest, file_obj, defaults)
                else:
                    file_defaults.update(
                        yarn.utils.resolve(file_obj.get('defaults', {}), **defaults))
                    deploy_service_files_file(host, service, file_obj, defaults)

            iter_dict(iterator, iterator.keys(), file_obj, defaults)
        else:
            iterator = yarn.utils.resolve(file_obj.get('iter', ['']), **file_defaults)
            if not isinstance(iterator, collections.Iterable):
                print "Error: The iterator 'iter' of the path '{}' of service '{}' in host '{}' is not iterable".format(file_obj.get('path', file_obj.get('dst', "<unknown>")), service, host)
                sys.exit(1)
            for item in iterator:
                if api.env.debug:
                    print "269", item, file_obj
                file_defaults["iter"] = item
                file_defaults.update(
                    yarn.utils.resolve(file_obj.get('defaults', {}), **file_defaults))
                deploy_service_files_file(host, service, file_obj, file_defaults)

    # Service enable, (re)start
    serviced = yarn.utils.resolve(
        yarn.query("$.service.'{service}'.service", **defaults), **defaults)
    servicesd = yarn.utils.resolve(
        yarn.query("$.service.'{service}'.services", **defaults), **defaults) or []
    if serviced:
        servicesd.append(serviced)
    for service in servicesd:
        if not api.env.dryrun:
            fabtools.require.service.restart(service)
        else:
            print "Demanding service: {}".format(service)

def deploy_service_script(host, service, defaults):
    """Execute an abitrary script on the host"""
    script = yarn.query("$.service.'{service}'.script", **defaults)
    if script and isinstance(script, (str, yarn.yaml.scalarstring.PreservedScalarString, yarn.yaml.Template)):
        script = script.format(defaults)
        remotepath = "{__tmpdir__}/{service}-execute".format(**defaults)
        if not api.env.dryrun:
            fabtools.require.files.file(
                path=remotepath,
                contents=script,
                mode='0700',
                verify_remote=False
            )
            api.run(remotepath)
        else:
            print "Script {} will be: \n{}".format(remotepath, script)

