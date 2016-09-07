#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Connects the jinja2 template engine
"""
from __future__ import print_function
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateSyntaxError
import sys
from ruamel import yaml
from .environment import env, query

FILTERS = env['template']['filters']
LOADER = None
ENVIRONMENT = None

def init():
    """Init template functionality"""
    global LOADER, ENVIRONMENT
    LOADER = FileSystemLoader(env["datastore"]["path"])
    ENVIRONMENT = Environment(loader=LOADER, line_statement_prefix='#%', line_comment_prefix='##')
    env['template']['filters'].update(ENVIRONMENT.filters)
    ENVIRONMENT.filters = env['template']['filters']
    env["template"].update({
        "loader": LOADER,
        "env": ENVIRONMENT,
    })

def jinja2Split(string, delimer=' '):
    return string.split(delimer)
FILTERS['split'] = jinja2Split

class Template(object):
    """Template object"""
    def __init__(self, template=None, filename=None):
        """
        Store query string
        """
        self.template = template
        self.filename = filename or ""
        if self.filename and not self.template:
            try:
                with open(self.filename, 'r') as filehandle:
                    self.template = filehandle.read()
            except IOError as err:
                print("An IOError occured", err)
                sys.exit(1)

    def __repr__(self):
        """
        Print string representation of the template
        """
        return "!template "+self.template
    def get_template(self):
        """
        Return the template string
        """
        return self.template
    def format(self, *k, **kw):
        """
        Returns the evaluated templates with the given parameters.
        """
        if len(k) == 1 and isinstance(k[0], dict):
            kw.update(k[0])
        def jinja2Query(querystr, **query_kw):
            newkw = {}
            newkw.update(kw)
            newkw.update(query_kw)
            return query(querystr, **newkw)
        def isdict(name):
            return isinstance(name, dict)
        kw['query'] = jinja2Query
        kw['isdict'] = isdict
        kw.update(env['template']['functions'])
        try:
            template = ENVIRONMENT.from_string(self.template)
            template.filename = self.filename
            return template.render(**kw)
        except TemplateSyntaxError as err:
            print("An rendering error occured {}:{}".format(
                self.filename, err.lineno), err)
            sys.exit(1)

def template_f(template=None, filename=None):
    """Create templates in a template"""
    return Template(template, filename)
env['template']['functions']['template'] = template_f

def template_constructor(loader, node):
    """
    Convert node as scalar from loader to a Template object
    """
    value = loader.construct_scalar(node)
    if isinstance(value, dict):
        return Template(**dict)
    else:
        return Template(value)
yaml.add_constructor(u'!template', template_constructor, yaml.RoundTripLoader)

def template_representer(dumper, data):
    """
    Convert Template object to a query string with tag
    """
    return dumper.represent_scalar(u'!template', data.template)
yaml.add_representer(Template, template_representer, yaml.RoundTripDumper)


