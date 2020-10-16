# -*- coding: utf-8  -*-
"""Setup script for anyhttp."""
#
# (C) John Vandenberg, 2015-2020
#
# Distributed under the terms of the MIT license.
#
import os
import sys

if 'test' in sys.argv and sys.version_info < (2, 7):
    import unittest
    import unittest2
    sys.modules['unittest'] = unittest2

from setuptools import setup

# anyhttp.supported_http_packages contains a dynamically determined list
# of clients supported on the python version, which is used to create
# a list of clients to add as dependencies for the tests.

import anyhttp

not_installable_links = {
    # no setup.py
    'httxlib': 'https://pypi.python.org/pypi/HttxLib',
    # pypi tarball is broken; setup.py doesnt install code
    'ultralite': 'https://github.com/cathalgarvey/ultralite',
}

nonpypi_dependency_links = [
    # not on pypi
    'git+https://github.com/mjohnsullivan/reqres#egg=reqres',
]

bugfix_dependency_links = [
    'git+https://github.com/jayvdb/basic_http@rename-dir#egg=BasicHttp',
]

dependency_links = []
dependency_links += nonpypi_dependency_links
dependency_links += bugfix_dependency_links

# 'jaraco.httplib2' is removed from PyPI
# 'yieldfrom.http.client' needs to be used as-is, whereas e.g.
# 'tornado.httpclient' is part of the 'tornado' package
http_packages = set([
    name if name in ['yieldfrom.http.client']
    else name.split('.')[0]
    for name in anyhttp.supported_http_packages
    if name not in ['jaraco.httplib2']
])

try:
    sys.pypy_version_info
except AttributeError:
    pass
else:
    # gevent doesnt compile on Travis-CI
    # urlgrabber causes 'maximum recursion depth exceeded' while
    # initialising pycurl, pycurl causes a StackOverflow (pypi and master):
    # https://github.com/pycurl/pycurl/issues/228
    http_packages -= set(['geventhttpclient', 'urlgrabber', 'pycurl'])

http_packages -= set(not_installable_links.keys())

if 'TEST_SKIP_PACKAGES' in os.environ:
    env_skip_packages = set(os.environ['TEST_SKIP_PACKAGES'].split(' '))
    http_packages -= env_skip_packages

test_deps = list(http_packages)

setup(
    name='anyhttp',
    version='0.1',
    description='Generic interface to access HTTP clients',
    long_description=open('README.rst').read(),
    maintainer='John Vandenberg',
    maintainer_email='jayvdb@gmail.com',
    license='MIT License',
    packages=['anyhttp'],
    dependency_links=dependency_links,
    test_suite="tests",
    tests_require=test_deps,
    classifiers=[
        'Topic :: Internet :: WWW/HTTP',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    use_2to3=False
)
