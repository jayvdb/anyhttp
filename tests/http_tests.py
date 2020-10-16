# -*- coding: utf-8 -*-
"""HTTP tests."""
import codecs
import os
import sys

import anyhttp

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    import testtools
    from testscenarios import with_scenarios
except ImportError:
    raise unittest.SkipTest("""
testscenarios.with_scenarios not found.
Please fetch and install testscenarios from:
https://code.launchpad.net/~jayvdb/testscenarios/0.4-with_scenarios
""")


if sys.version_info[0] > 2:
    PY3 = True
    basestring = (str, )
    unicode = str
else:
    PY3 = False

no_redirect_support = set([
    'pycurl', 'fido', 'httq', 'async_http', 'webob', 'urlfetch',
    'httputils', 'tinydav', 'hyper', 'geventhttpclient', 'dugong',
    'yieldfrom.http.client',
])

# No longer exists on PyPI and SCM deleted
revoked_packages = ['jaraco.httplib2']
# These two cause the following exception if run as scenario:
# NotImplementedError: gevent is only usable from a single thread
threading_problems = ['asynchttp', 'httxlib']
streaming_problems = ['async_http']

anyhttp.verbose = False

httpbin_url = 'http://httpbingo.org'


class TestBase(testtools.TestCase):

    """Base test case for testing various HTTP client implementation."""

    def setUp(self):
        """Set up anyhttp."""
        anyhttp.http = None
        anyhttp.loaded_http_packages = None
        super(TestBase, self).setUp()

    @property
    def request_url(self):
        raise RuntimeError('abstract property')

    def check_response(self, value):
        raise RuntimeError('abstract method')

    def _load_package(self, force='FORCE_TEST' in os.environ):
        name = self.package  # load name from scenario

        if name in threading_problems and not force:
            self.skipTest('%s causes threading problems' % name)

        if name in anyhttp.unsupported_http_packages and not force:
            self.skipTest('%s is not supported on this platform' % name)

        try:
            __import__(name)
        except ImportError as e:
            self.skipTest('%s could not be imported: %r' % (name, e))

        self.assertIn(name, sys.modules)

        added = False
        if force and name not in anyhttp.supported_http_packages:
            anyhttp.supported_http_packages.add(name)
            added = True

        anyhttp.detect_loaded_package()

        if added:
            anyhttp.supported_http_packages.remove(name)

        self.assertIn(name, anyhttp.package_handlers.keys())
        self.assertIn(name, anyhttp.loaded_http_packages)

    def select_package(self):
        name = self.package  # load name from scenario
        self._load_package()
        anyhttp.loaded_http_packages = set([name])

    def do_get_text(self):
        self.select_package()

        url = self.request_url

        if self.package in streaming_problems and url.endswith('/utf8'):
            if 'FORCE_TEST' not in os.environ:
                self.skipTest('%s causes streaming problems' % self.package)

        result = anyhttp.get_text(self.request_url)

        self.assertIsNotNone(result)

        self.assertIsInstance(result, basestring)

        self.check_response(result)

    def do_get_bin(self):
        self.select_package()

        result = anyhttp.get_binary(self.request_url)

        self.assertIsNotNone(result)

        self.assertIsInstance(result, bytes)

        self.check_response(result)


class TestAll(TestBase):

    """Set scenarios to include all clients."""

    expected_file = None

    scenarios = [(name.replace('.', '_'), {'package': name})
                 for name in anyhttp.package_handlers.keys()
                 # Silently ignore packages that cant be tested
                 if name not in revoked_packages
                 ]


class _TestGetBase(object):

    expected_file = 'utf8.txt'

    @classmethod
    def setUpClass(cls):
        with codecs.open(os.path.join(os.path.split(__file__)[0],
                                      cls.expected_file),
                         'r', 'utf8') as f:
            cls.expected_value = f.read()
            if 'httpbingo.org' in httpbin_url:
                cls.expected_value = cls.expected_value + '\n'

    @property
    def request_url(self):
        return httpbin_url + '/encoding/utf8'

    def check_response(self, value):
        # assertEqual will dump out lots of unreadable information
        self.assertTrue(value)
        self.assertEqual(value, self.expected_value)


@with_scenarios()
class TestGetText(_TestGetBase, TestAll):

    """Test all clients for text requests."""

    test = TestBase.do_get_text


@with_scenarios()
class TestGetBin(TestAll):

    """Test all clients for binary requests."""

    expected_file = 'pig.png'

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(os.path.split(__file__)[0],
                               cls.expected_file),
                  'rb') as f:
            cls.expected_value = f.read()

    @property
    def request_url(self):
        return httpbin_url + '/image/png'

    test = TestBase.do_get_bin

    def check_response(self, value):
        # assertEqual will dump out lots of unreadable information
        self.assertTrue(value)
        self.assertEqual(value, self.expected_value)


@with_scenarios()
class TestRelativeRedirects(TestAll):

    """Test all clients for relative redirects."""

    @property
    def request_url(self):
        return httpbin_url + '/relative-redirect/2'

    def check_response(self, value):
        if self.package in no_redirect_support:
            self.assertEqual('', value)
        else:
            self.assertTrue(value)
            self.assertIn(httpbin_url + '/get', value)
            self.assertFalse('If not click the link' in value)

    test = TestBase.do_get_text


class TestAbsoluteRedirects(TestRelativeRedirects):

    """Test all clients for absolute redirects."""

    @property
    def request_url(self):
        return httpbin_url + '/absolute-redirect/2'


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
