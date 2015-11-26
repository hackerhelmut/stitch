#!/usr/bin/env python
import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='stitch',
    version='0.5.0',
    author="Rolf Meyer",
    author_email="rmeyer@embeddedfactor.com",
    description=("An automation utility to deploy server configurations "
                 "from a YAML datastore."),
    license="Apache License 2.0 (Apache-2.0)",
    keywords="YAML Automation Deployment",
    url="http://github.com/embeddedfactor/yarn",
    packages=['stitch'],
    scripts=['bin/stitch'],
    long_description=read('README.md'),
    install_requires=[
        'yarn',
        'Fabric==1.10.2',
        'Jinja2==2.8',
    ],
    dependency_links=[
        'git+git@github.com:hackerhelmut/ObjectPath.git#egg=objectpath-master',
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software Licens",
    ],
)
